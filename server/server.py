import socket, threading, time , random , pygame , math
from const import *
from server_data import Tank, Attack, Wall

class client_state:
    def __init__(self,last_time, is_active):
        self.last_time = last_time
        self.is_active = is_active


class Server:
    def __init__(self, max_player_in_room = PLAYER_COUNT ):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 1234))
        print("server started on port 1234")
        self.rooms = []
        self.lock = threading.Lock()
        self.clients = [] # addr
        self.max_players_in_room = max_player_in_room

    def start(self):
        threading.Thread(target = self.show_state , daemon = True).start()
        threading.Thread(target = self.clean_dead_rooms , daemon = True).start()

        while True:
            data , addr = self.recv()
            if not addr or not data: continue

            self.register(addr)

            if data == START_GAME:
                self.join_room(addr)
            else:
                room = self.find_room(addr)
                if room:
                    room.handle_input(addr, data)


    def recv(self):
        try:
            data, addr = self.sock.recvfrom(2048)
            print(f"got from{addr} -->> {len(data)}|" + data.decode())
            return (data,addr)
        except Exception as e:
            print(e)
            return (None , None)


    def register(self, addr):
        with self.lock:
            if addr not in self.clients:
                self.clients.append(addr)


    def clean_dead_rooms(self):
        while True:
            with self.lock:
                for i in self.rooms[:]:
                    if i.running == False:
                        self.rooms.remove(i)
            time.sleep(1)


    def join_room(self, addr):
        with self.lock:
            for room in self.rooms:
                if room.player_count < room.max_players:
                    room.add_player(addr)
                    return

            room = Room(self.sock, self, self.max_players_in_room)
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
              f"default players count in each room: {self.max_players_in_room}\n"
              f"=================================\n"
              f"{state}\n")




class Room(threading.Thread):
    def __init__(self, sock, server, max_player ):
        super().__init__(daemon=True)
        self.server = server
        self.max_players = max_player
        self.sock = sock
        self.players = {}      # addr -> Tank
        self.players_timer = {}# addr -> time
        self.inputs = {}       # addr -> last key
        self.attacks = []      #(addr, Attack)
        self.player_count = 0
        self.running = True
        self.walls = self.create_maze_walls()
        self.lock = threading.Lock()
        self.original_players = []# addr


    def create_maze_walls(self):
        walls = []
        W, H = SCREEN_SIZE

        # גבולות חיצוניים
        walls.append(Wall(0, 0, W, WALL_SIZE))  # עליון
        walls.append(Wall(0, H - WALL_SIZE, W, WALL_SIZE))  # תחתון
        walls.append(Wall(0, 0, WALL_SIZE, H))  # שמאל
        walls.append(Wall(W - WALL_SIZE, 0, WALL_SIZE, H))  # ימין

        # קיר מרכזי אופקי
        walls.append(Wall(W * 0.1, H * 0.45, W * 0.8, WALL_SIZE))

        # קיר מרכזי אנכי
        walls.append(Wall(W * 0.48, H * 0.1, WALL_SIZE, H * 0.8))

        # חדר שמאל עליון
        walls.append(Wall(W * 0.1, H * 0.1, W * 0.25, WALL_SIZE))
        walls.append(Wall(W * 0.1, H * 0.1, WALL_SIZE, H * 0.25))

        # חדר ימין עליון
        walls.append(Wall(W * 0.65, H * 0.1, W * 0.25, WALL_SIZE))
        walls.append(Wall(W * 0.9 - WALL_SIZE, H * 0.1, WALL_SIZE, H * 0.25))

        # מסדרון עליון מפותל
        walls.append(Wall(W * 0.25, H * 0.25, W * 0.15, WALL_SIZE))
        walls.append(Wall(W * 0.6, H * 0.25, W * 0.15, WALL_SIZE))

        # חדר שמאל תחתון
        walls.append(Wall(W * 0.1, H * 0.65, W * 0.25, WALL_SIZE))
        walls.append(Wall(W * 0.1, H * 0.65, WALL_SIZE, H * 0.25))

        # חדר ימין תחתון
        walls.append(Wall(W * 0.65, H * 0.65, W * 0.25, WALL_SIZE))
        walls.append(Wall(W * 0.9 - WALL_SIZE, H * 0.65, WALL_SIZE, H * 0.25))

        # מסדרון תחתון מפותל
        walls.append(Wall(W * 0.25, H * 0.55, W * 0.15, WALL_SIZE))
        walls.append(Wall(W * 0.6, H * 0.55, W * 0.15, WALL_SIZE))

        # מחיצה קטנה באמצע (לקרבות)
        walls.append(Wall(W * 0.45, H * 0.45, W * 0.1, WALL_SIZE))

        return walls

    def add_player(self, addr):
        with self.lock:
            x, y = random.randint(100, 800), random.randint(100, 800)
            tank = Tank(x, y, 25 * (SCREEN_SIZE[0] / 800), 25 * (SCREEN_SIZE[1] / 650), speed=2, hp=6)
            reposition = True
            while reposition:
                reposition = False
                for i in self.walls:
                    if i.hitbox.colliderect(tank.get_rect()):
                        tank.x = random.randint(100, 800)
                        tank.y = random.randint(100, 800)
                        reposition = True

            self.original_players.append(addr)

            self.players[addr] = tank
            self.inputs[addr] = "NONE"
            self.player_count += 1
            self.players_timer[addr] = time.time()
            print("player joined room:", addr)


    def handle_input(self, addr, data):
        with self.lock:
            msg = data.decode()
            self.players_timer[addr] = time.time()
            if msg.startswith("INPUT|"):
                key = msg.split("|", 1)[1]
                self.inputs[addr] = key



    def run(self):
        while self.running:
            if self.player_count == self.max_players:
                self.update_all()
                self.send_state()
            else:
                self.player_time_out()
                for i in self.players.keys():
                    self.send(WAIT,i)

            time.sleep(1 / FPS)


    def update_all(self):

        for addr, player in list(self.players.items()):
            with self.lock:
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
                with self.lock:
                    player.last_attack = time.time()
                    self.attacks.append((addr, Attack(player.x, player.y, player.rotation)))

        with self.lock:
            for addr, atk in self.attacks[:]:
                audio = atk.update(self.walls, self.players)
                self.send_sound(audio)

                if atk.is_finished():
                    self.attacks.remove((addr,atk))

                if atk.is_out_of_bounds():
                    self.attacks.remove((addr, atk))
                    continue

            for addr1 , atk1 in self.attacks[:]:
                for addr2 , atk2 in self.attacks[:]:
                    if atk1 != atk2 and atk1.get_rect().colliderect(atk2.get_rect()):
                        self.attacks.remove((addr1,atk1))
                        self.attacks.remove((addr2,atk2))
                        self.send_sound(audio_type.HIT_PLAYER)

        with self.lock:
            for addr , player in list(self.players.items()):
                if player.hp <= 0:
                    self.send(LOSE_GAME,addr)
                    self.remove_payer(addr)

            if self.player_count <= 1:
                for addr, player in list(self.players.items()):
                    self.send(WIN_GAME,addr)
                    self.remove_payer(addr)

        self.player_time_out()


    def player_time_out(self):
        with self.lock:
            for addr , timer in list(self.players_timer.items()):
                if time.time() - timer > TIME_BEFORE_REMOVE:
                    self.remove_payer(addr)


    def remove_payer(self, addr):
        if addr in list(self.players.keys()):
            del self.players[addr]
            self.server.clients.remove(addr)
            del self.players_timer[addr]

            if self.max_players == self.player_count :# אם שחקן עוזב במהלך המשחק
                self.max_players -= 1

            self.player_count -= 1

        if self.player_count == 0:
            self.running = False


    def send_sound(self,type):
        if not type: return

        for i in self.players.keys():
            self.send(AUDIO + str(type).encode(),i)


    def send_state(self):
        msg = "STATE|"

        for addr, p in self.players.items():
            msg += f"PLAYER,{p.x},{p.y},{p.width},{p.height},{p.hp},{p.rotation}|"

        for player, atk in self.attacks:
            msg += f"ATTACK,{atk.x},{atk.y},{atk.rotation}|"

        data = msg.encode()
        for addr in self.players.keys():
            self.send(data, addr)
    
    def send(self,msg , addr):
        self.sock.sendto(msg,addr)

if __name__ == "__main__":
    s = Server()
    s.start()
