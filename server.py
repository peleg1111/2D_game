import socket, threading, time , random , pygame
from const import *
from const_class import Tank, Attack
from game_manager import GameState


class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 1234))
        print("server started on port 1234")
        self.rooms = []
        self.lock = threading.Lock()

    def start(self):
        threading.Thread(target = self.show_state , daemon = True).start()

        while True:
            data, addr = self.sock.recvfrom(2048)
            print(f"got from{addr} -->> {len(data)}|" + data.decode())

            if data == START_GAME:
                self.join_room(addr)
            else:
                room = self.find_room(addr)
                if room:
                    room.handle_input(addr, data)

    def join_room(self, addr):
        with self.lock:
            for room in self.rooms:
                if room.player_count < PLAYER_COUNT:
                    room.add_player(addr)
                    return

            room = Room(self.sock)
            room.add_player(addr)
            room.start()
            self.rooms.append(room)

    def find_room(self, addr):
        with self.lock:
            for room in self.rooms:
                if addr in room.players:
                    return room
        return None


    def show_state(self):
        while True:
            with self.lock:
                print(self.State())
            time.sleep(1)

    def State(self):
        state = ""
        for num , i in enumerate(self.rooms):
            state += (f"\n       room{num + 1}        \n"
                      f"players count: {i.player_count}\n"
                      f"attacks count: {len(i.attacks)}\n")

        return (f"=========  SERVER  ============\n"
              f"room count: {len(self.rooms)}\n"
              f"players count: {PLAYER_COUNT}\n"
              f"=================================\n"
              f"{state}\n")

class Wall:
    def __init__(self, x, y, w, h):
        self.hitbox = pygame.Rect(x, y, w, h)


class Room(threading.Thread):
    def __init__(self, sock):
        super().__init__(daemon=True)
        self.sock = sock
        self.players = {}      # addr -> Tank
        self.inputs = {}       # addr -> last key
        self.attacks = []      #(addr, Attack)
        self.player_count = 0
        self.running = True
        self.walls = self.create_maze_walls()
        self.lock = threading.Lock()

    def create_maze_walls(self):
        walls = []
        T = 12  # עובי קיר
        W, H = SCREEN_SIZE

        # גבולות חיצוניים
        walls.append(Wall(0, 0, W, T))  # עליון
        walls.append(Wall(0, H - T, W, T))  # תחתון
        walls.append(Wall(0, 0, T, H))  # שמאל
        walls.append(Wall(W - T, 0, T, H))  # ימין

        # קיר מרכזי אופקי
        walls.append(Wall(W * 0.1, H * 0.45, W * 0.8, T))

        # קיר מרכזי אנכי
        walls.append(Wall(W * 0.48, H * 0.1, T, H * 0.8))

        # חדר שמאל עליון
        walls.append(Wall(W * 0.1, H * 0.1, W * 0.25, T))
        walls.append(Wall(W * 0.1, H * 0.1, T, H * 0.25))

        # חדר ימין עליון
        walls.append(Wall(W * 0.65, H * 0.1, W * 0.25, T))
        walls.append(Wall(W * 0.9 - T, H * 0.1, T, H * 0.25))

        # מסדרון עליון מפותל
        walls.append(Wall(W * 0.25, H * 0.25, W * 0.15, T))
        walls.append(Wall(W * 0.6, H * 0.25, W * 0.15, T))

        # חדר שמאל תחתון
        walls.append(Wall(W * 0.1, H * 0.65, W * 0.25, T))
        walls.append(Wall(W * 0.1, H * 0.65, T, H * 0.25))

        # חדר ימין תחתון
        walls.append(Wall(W * 0.65, H * 0.65, W * 0.25, T))
        walls.append(Wall(W * 0.9 - T, H * 0.65, T, H * 0.25))

        # מסדרון תחתון מפותל
        walls.append(Wall(W * 0.25, H * 0.55, W * 0.15, T))
        walls.append(Wall(W * 0.6, H * 0.55, W * 0.15, T))

        # מחיצה קטנה באמצע (לקרבות)
        walls.append(Wall(W * 0.45, H * 0.45, W * 0.1, T))

        return walls

    def add_player(self, addr):
        x, y = random.randint(200, 500), random.randint(100, 500)
        tank = Tank(x, y, 25, 25, speed=3, hp=5)
        reposition = True
        while reposition:
            reposition = False
            for i in self.walls:
                if i.hitbox.colliderect(tank.get_rect()):
                    tank.x = random.randint(200, 500)
                    tank.y = random.randint(100, 500)
                    reposition = True

        self.players[addr] = tank
        self.inputs[addr] = "NONE"
        self.player_count += 1
        print("player joined room:", addr)

    def handle_input(self, addr, data):
        msg = data.decode()
        if msg.startswith("INPUT|"):
            key = msg.split("|", 1)[1]
            self.inputs[addr] = key

    def run(self):
        while self.running:
            if self.player_count == PLAYER_COUNT:
                self.update_world()
                self.send_state()
            time.sleep(1 / FPS)

    def update_world(self):
        with self.lock:
            for addr, player in self.players.items():
                key = self.inputs.get(addr, "NONE")

                if 'W' in key:
                    player.move(0.75, self.walls, [self.players[i] for i in self.players.keys() if i != addr])

                if 'S' in key:
                    player.move(-0.75, self.walls, [self.players[i] for i in self.players.keys() if i != addr])

                if 'A' in key:
                    player.rotate(-2.5)

                if 'D' in key:
                    player.rotate(2.5)

                if  "!" in key and time.time() - player.last_attack > player.cooldown:
                    player.last_attack = time.time()
                    self.attacks.append((addr, Attack(player.x, player.y, player.rotation)))

            for addr, atk in self.attacks[:]:
                atk.update(self.walls, self.players)

                if atk.is_finished():
                    self.attacks.remove((addr,atk))

                if atk.is_out_of_bounds():
                    self.attacks.remove((addr, atk))
                    continue
            for addr , player in list(self.players.items())[:]:
                if player.hp <= 0:
                    del self.players[addr]
                    self.sock.sendto(LOSE_GAME,addr)
            if len(self.players.keys()) == 1:
                for i in list(self.players.keys()):
                    self.sock.sendto(WIN_GAME,i)
                    del self.players[i]

    def send_state(self):
        msg = "STATE|"

        for addr, p in self.players.items():
            msg += f"PLAYER,{p.x},{p.y},{p.width},{p.height},{p.hp},{p.rotation}|"

        for player, atk in self.attacks:
            msg += f"ATTACK,{atk.x},{atk.y},{atk.rotation}|"

        data = msg.encode()
        for addr in self.players.keys():
            self.sock.sendto(data, addr)

if __name__ == "__main__":
    s = Server()
    s.start()
