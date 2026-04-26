import socket, threading, time , random , pygame
from const import *
from const_class import Tank, Attack

class Server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 1234))
        print("server started on port 1234")
        self.rooms = []
        self.lock = threading.Lock()

    def start(self):
        while True:
            data, addr = self.sock.recvfrom(2048)

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

        self.walls = [
            Wall(-9, 0, 9, SCREEN_SIZE[1]),
            Wall(SCREEN_SIZE[0], 0, 9, SCREEN_SIZE[1]),
            Wall(0, SCREEN_SIZE[1], SCREEN_SIZE[0], 9),
            Wall(0, 0, SCREEN_SIZE[0], 9),
            Wall(SCREEN_SIZE[0] / 4, SCREEN_SIZE[1] / 2, SCREEN_SIZE[0] / 2, 9)
        ]

    def add_player(self, addr):
        x, y = random.randint(200, 500), random.randint(100, 500)
        self.players[addr] = Tank(x, y, 25, 25, speed=3, hp=5)
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
        for addr, player in self.players.items():
            key = self.inputs.get(addr, "NONE")

            if 'W' in key:
                player.move(0.6, self.walls, [self.players[i] for i in self.players.keys() if i != addr])

            if 'S' in key:
                player.move(-0.6, self.walls, [self.players[i] for i in self.players.keys() if i != addr])

            if 'A' in key:
                player.rotate(-2)

            if 'D' in key:
                player.rotate(2)

            if  "!" in key and time.time() - player.last_attack > player.cooldown:
                player.last_attack = time.time()
                self.attacks.append((addr, Attack(player.x, player.y, player.rotation)))

        for addr, atk in self.attacks[:]:
            atk.update(self.walls)
            if atk.is_finished():
                self.attacks.remove((addr,atk))

            if atk.is_out_of_bounds():
                self.attacks.remove((addr, atk))
                continue

            for addr, player in self.players.items():
                if addr == addr:
                    continue
                if player.is_hit_by(atk):
                    player.hp -= 1
                    self.attacks.remove((addr, atk))
                    break

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
