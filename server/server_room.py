import time , random , threading, socket , os, sys , math

sys.path.insert(0, os.path.dirname(__file__))# רשימת הקבצים שimport מחפש בהם קבצים להרצה
#  מכניס את התיקייה שבה נמצא הקובץ לרשימה כך שimport יוכל למצוא אותו ולהריץ מתוך הcmd

from server_data import Tank, Attack, Wall
from const import *


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
        self.ack_received = { } # ACK_TYPE --> [addr , ....]
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
            self.safe_send(addr, WALLS + b'|' + str(self.maze_num).encode(), WALLS)


    def handle_input(self, addr, data):
        with self.lock:

            msg = data.decode()
            self.players_timer[addr] = time.time()
            if msg.startswith(INPUT.decode()):
                key = msg.split("|", 1)[1]
                self.inputs[addr] = key

            if msg.startswith('ACK'):
                ack_type = msg.split("|")[1]
                if ack_type not in self.ack_received:
                    self.ack_received[ack_type] = []
                if addr not in self.ack_received[ack_type]:
                    self.ack_received[ack_type].append(addr)


    def run(self):
        threading.Thread( target = self.send_end_msg ,daemon = True ).start()

        while self.running:
            if self.player_count == self.max_players:
                self.update_all()
                self.send_state()
            else:
                self.player_time_out()
                with self.lock:
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
                    if time.time() - ttl > TIME_BEFORE_REMOVE:
                        del self.players_last_msg[addr]
            if not self.players_last_msg and not self.running:
                return

            time.sleep(1 / FPS)


    def safe_send(self,addr,msg , ack_type ,block = False):
        t = threading.Thread(target=self._safe_send,args=(addr,msg, ack_type), daemon= True)
        t.start()

        if block:
            t.join()

    def _safe_send(self, addr, msg, ack_type):
        ack_key = ack_type.decode() if isinstance(ack_type, bytes) else ack_type
        deadline = time.time() + 3 * TIME_BEFORE_REMOVE
        while time.time() < deadline:
            with self.lock:
                if addr not in self.players:
                    return
                if ack_key in self.ack_received and addr in self.ack_received[ack_key]:
                    self.ack_received[ack_key].remove(addr)
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
        msg = f"{STATE}{self.next_seq_num}|"
        self.next_seq_num += 1
        for addr, p in self.players.items():
            msg += f"PLAYER,{p.x},{p.y},{p.width},{p.height},{p.hp},{p.rotation}|"

        for player, atk in self.attacks:
            msg += f"ATTACK,{atk.x},{atk.y},{atk.rotation}|"

        data = msg.encode()
        for addr in self.players.keys():
            self.send(data, addr)


    def send(self,msg , addr, DROP_RATE = 0.1, CHANGE_RATE = 0.14):
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

        if not self.server.aes.get(addr, None) is None:
            msg = self.server.aes[addr].encrypt(msg)

        self.sock.sendto(msg,addr)
