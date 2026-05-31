__author__ = 'Peleg Etzioni'
import socket, threading, time , random , pygame , math
from const import *
from server_data import Tank, Attack, Wall
from server_UI import Server_ui


class client_state:
    def __init__(self,last_time, is_active):
        self.last_time = last_time
        self.is_active = is_active


class Server:
    def __init__(self, max_player_in_room = PLAYER_COUNT ):

        self.sock = self.create_sock()
        self.rooms = []
        self.lock = threading.Lock()
        self.clients = [] # addr
        self.max_players_in_room = max_player_in_room
        self.active = True


    def create_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 1234))
        sock.settimeout(2)
        print("server started on port 1234")
        return sock

    def start(self):
        threading.Thread(target = self.show_state , daemon = True).start()
        threading.Thread(target = self.clean_dead_rooms , daemon = True).start()

        while self.active:
            data , addr = self.recv()
            if not addr or not data: continue

            self.register(addr)

            if data == START_GAME and not self.find_room(addr):
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

        except socket.timeout:
            return (None, None)

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
        self.maze_num = random.randint(1,3)
        self.walls = self.create_maze_walls(self.maze_num)
        self.lock = threading.Lock()
        self.original_players = []# addr
        self.players_last_msg = {} # addr --> [msg( win / lose ), time]
        self.ack_received = set()
        self.next_seq_num = 0

    def create_maze_walls(self, maze_num):
        maze = ALL_MAZES.get(maze_num, MAZE_1)
        return [
            Wall(x, y, width, height) for x, y, width, height in maze
        ]



    def add_player(self, addr):
        with self.lock:
            x, y = random.randint(150, 700), random.randint(150, 700)
            tank = Tank(x, y, 25 * (SCREEN_SIZE[0] / 800), 25 * (SCREEN_SIZE[1] / 650), speed=2, hp=6)
            reposition = True
            while reposition:
                reposition = False
                for i in self.walls:
                    if i.hitbox.colliderect(tank.get_rect()):
                        tank.x = random.randint(100, SCREEN_SIZE[0] - 100)
                        tank.y = tank.y = random.randint(100, SCREEN_SIZE[1] - 100)
                        reposition = True

                for _addr,_tank in self.players.items():
                    if _addr == addr: continue
                    distance = math.sqrt((_tank.x - tank.x)**2 + (_tank.y - tank.y)**2)
                    print(f'{distance = } m')
                    if distance < 200 and addr != _addr:
                        tank.x = random.randint(100, SCREEN_SIZE[0] - 100)
                        tank.y = tank.y = random.randint(100, SCREEN_SIZE[1] - 100)
                        reposition = True


            self.original_players.append(addr)

            self.players[addr] = tank
            self.inputs[addr] = "NONE"
            self.player_count += 1
            self.players_timer[addr] = time.time()
            print("player joined room:", addr)
            self.safe_send(addr, WALLS + str(self.maze_num).encode())

    def handle_input(self, addr, data):
        with self.lock:
            msg = data.decode()
            self.players_timer[addr] = time.time()
            if msg.startswith("INPUT|"):
                key = msg.split("|", 1)[1]
                self.inputs[addr] = key

            if msg == 'ACK':
                self.ack_received.add(addr)



    def run(self):
        threading.Thread( target = self.send_end_msg ,daemon = True ).start()

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
                    atk = Attack(player.x, player.y, player.rotation)
                    for wall in self.walls:
                        if wall.hitbox.colliderect(atk.get_rect()):
                            atk = None
                            break
                    if atk:
                        self.attacks.append((addr, Attack(player.x, player.y, player.rotation)))

        with self.lock:
            for addr, atk in self.attacks[:]:
                atk.update(self.walls, self.players)

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

        with self.lock:
            for addr , player in list(self.players.items()):
                if player.hp <= 0:
                    self.players_last_msg[addr] = [LOSE_GAME , time.time()]
                    self.send(LOSE_GAME, addr)
                    self.remove_payer(addr)

            if self.player_count <= 1:
                for addr, player in list(self.players.items()):
                    self.players_last_msg[addr] = [WIN_GAME , time.time()]
                    self.send(WIN_GAME,addr)
                    self.remove_payer(addr)

        self.player_time_out()


    def player_time_out(self):
        with self.lock:
            for addr , timer in list(self.players_timer.items()):
                if time.time() - timer > TIME_BEFORE_REMOVE:
                    self.remove_payer(addr)


    def send_end_msg(self):
        while True:
            with self.lock:
                for addr, (msg, ttl) in list(self.players_last_msg.items()):
                    self.send(msg, addr)
                    if time.time() - ttl > 3:
                        del self.players_last_msg[addr]
            if not self.players_last_msg and not self.running:
                return

            time.sleep(1 / FPS)


    def safe_send(self,addr,msg):
        threading.Thread(target=self._safe_send,args=(addr,msg), daemon= True).start()


    def _safe_send(self, addr, msg):
        deadline = time.time() + 10  # timeout
        while time.time() < deadline:
            with self.lock:
                if addr not in self.players:  # השחקן התנתק
                    return
                if addr in self.ack_received:
                    self.ack_received.discard(addr)
                    return
                self.send(msg, addr)
            time.sleep(1 / FPS)


    def remove_payer(self, addr):
        if addr in list(self.players.keys()):
            del self.players[addr]
            self.server.clients.remove(addr)
            del self.players_timer[addr]

            if self.max_players == self.player_count : # אם שחקן עוזב במהלך המשחק
                self.max_players -= 1

            self.player_count -= 1

        if self.player_count == 0:
            self.running = False


    def send_state(self):
        msg = f"STATE{self.next_seq_num}|"
        self.next_seq_num += 1
        for addr, p in self.players.items():
            msg += f"PLAYER,{p.x},{p.y},{p.width},{p.height},{p.hp},{p.rotation}|"

        for player, atk in self.attacks:
            msg += f"ATTACK,{atk.x},{atk.y},{atk.rotation}|"

        data = msg.encode()
        for addr in self.players.keys():
            self.send(data, addr)


    def send(self,msg , addr,DROP_RATE = 0.3, CHANGE_RATE = 0.6):
        msg = msg.encode() if isinstance(msg, str) else msg

        num = random.random()
        if num < DROP_RATE:  # מדמה איבוד של הודעות ברשת
            print(f"msg lost --> {msg}")
            return

        if num < CHANGE_RATE:  # מדמה שינוי של הודעות ברשת
            arr = list(msg.decode())
            random.shuffle(arr)
            msg = "".join(arr).encode()
            print(f"\n\nmsg changed --> {msg}\n\n")

        print(f"sent --> {addr} --> {msg}")
        self.sock.sendto(msg,addr)




if __name__ == "__main__":
    server = Server()
    server_ui = Server_ui(server)
    t = threading.Thread(target=server.start, daemon= True)
    t.start()
    server_ui.mainloop()
    t.join()
