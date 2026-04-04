import socket ,time
import threading

from const import *


class Server:
    def __init__(self):
        self.socket = self.create_socket()
        self.rooms = []
        self.players = []
        self.run = True
        self.lock = threading.Lock()
        threading.Thread(target= self.del_empty_room, daemon= True).start()

    def wait_for_connection(self):
        while True:
            data,addr = self.socket.recvfrom(1024)
            print(f"{len(data)}|{addr}|{data}")
            # אם השחקן לא מחובר
            if addr not in self.players:
                if data == START_GAME:
                    with self.lock:
                        self.players.append(addr)

                    self.find_player_room(addr)
                    self.socket.sendto(ACK,addr)
                else:
                    self.socket.sendto(CONNECTION_FAIL,addr)
            else:
                room = self.find_room(addr)
                if not room:
                    self.socket.sendto(CONNECTION_FAIL,addr)
                else:
                    room.handle_msg(addr,data)
            self.print_server_state()


    def find_room(self,addr):
        with self.lock:
            for room in self.rooms:
                if addr in room.players:
                    return room
        return None

    def find_player_room(self, addr):
        with self.lock:
            # מחפשים חדר קיים עם מקום
            for room in self.rooms:
                if room.count_players < 2:
                    room.add_player(addr)
                    return

            # יוצרים חדר חדש
            room = Room(addr, self.socket)
            self.rooms.append(room)
            room.start()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 1234))
        return sock

    def del_empty_room(self):
        while self.run:
            with self.lock:
                for room in self.rooms:
                    if room.count_players == 0:
                        self.rooms.remove(room)
            time.sleep(3)

    def print_server_state(self):
        with self.lock:
            print("\n========== SERVER STATE ==========")
            print(f"total players: {len(self.players)}")
            print(f"players: {self.players}")

            print(f"total rooms: {len(self.rooms)}")
            for i, room in enumerate(self.rooms):
                print(f"\n--- room {i} ---")
                print(f"players in room: {room.players}")
                print(f"count players: {room.count_players}")

                with room.lock:
                    for addr, (playerData, attacks) in room.game_data.items():
                        print(f" Player {addr}:")
                        if playerData:
                            print(
                                f"   Pos: {playerData.pos.x},{playerData.pos.y}  Size:{playerData.pos.width}x{playerData.pos.height}  HP:{playerData.hp}",
                                f" Rotation {playerData.pos.rotation}")
                        else:
                            print("   No PLAYER_DATA yet")

                        if attacks:
                            print("   Attacks:")
                            for atk in attacks:
                                print(f"     Attack ID {atk.id}: Pos({atk.pos.x},{atk.pos.y}) Speed:{atk.speed}")
                        else:
                            print("   No attacks")

            print("=================================\n")


class Room(threading.Thread):
    def __init__(self, player , server_sock):
        threading.Thread.__init__(self)
        self.players = []
        self.count_players = 0
        self.socket = server_sock
        self.Run = True
        # addr : [ GAME_DATA , ATTACK_DATA[] ]
        self.game_data = {}
        self.lock = threading.Lock()
        self.add_player(player)

    def add_player(self,addr):
        with self.lock:
            self.players.append(addr)
            self.count_players += 1
            self.game_data[addr] = [None , []]

    def run(self):
        while self.Run:
            with self.lock:
                count = self.count_players
                players = self.players[:]

            if count == 0:
                self.Run = False
                break

            if count < 2:
                for player in players:
                    self.socket.sendto(WAIT, player)
                time.sleep(0.5)
                continue

            info = self.str().encode()
            for player in players:
                self.socket.sendto(info, player)
            time.sleep(1 / FPS)

    def handle_msg(self, addr, msg):
        # GAME|TYPE|DATA
        parts = msg.split(b'|', 2)
        if len(parts) < 3:
            return

        header, msg_type, info = parts

        if header != GAME:
            return

        with self.lock:
            if msg_type == PLAYER_DATA:
                data = info
                if self.game_data[addr][0] == None:
                    self.game_data[addr][0] = GameData(data)
                else:
                    self.game_data[addr][0].update(data)
                return

            if msg_type == ATTACK_POS:
                data = info
                attack = AttackData(data)
                # מחפשים התקפה עם אותו id ומעדכנים אחרת מוסיפים חדשה
                for _attack in self.game_data[addr][1]:
                    if attack.id == _attack.id:
                        _attack.update(data)
                        break
                else:
                    self.game_data[addr][1].append(attack)

    def str(self):
        with self.lock:
            info = INFO.decode() + "|"
            for addr, (player_data, attacks) in self.game_data.items():
                if player_data is not None:
                    info += f"PLAYER{addr}," + player_data.str() + "|"
                for atk in attacks:
                    info += "ATTACK," + atk.str() + f",{atk.speed},{atk.id}|"
                info += "\n"
        return info


class Pos:
    def __init__(self, x, y, width, height,rotation):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation

    def str(self):
        return ','.join([
            str(self.x),
            str(self.y),
            str(self.width),
            str(self.height),
            str(self.rotation)
        ])

class GameData:
    def __init__(self ,msg):
        if isinstance(msg , bytes):
            msg = msg.decode()

        msg = msg.split(',')
        self.pos = Pos(int(msg[0]),int(msg[1]),int(msg[2]),int(msg[3]),int(msg[5]))
        self.hp = int(msg[4])


    def update(self,msg):
        if isinstance(msg , bytes):
            msg = msg.decode()
        parts = msg.split(',')

        self.pos.x = int(parts[0])
        self.pos.y = int(parts[1])
        self.pos.width = int(parts[2])
        self.pos.height = int(parts[3])
        self.hp = int(parts[4])
        self.pos.rotation = int(parts[5])

    def str(self):
        return self.pos.str()

class AttackData:
    def __init__(self ,msg):
        if isinstance(msg , bytes):
            msg = msg.decode()
        msg = msg.split(',')

        self.pos = Pos(int(msg[0]),int(msg[1]),int(msg[2]),int(msg[3]),int(msg[6]))
        self.speed = int(msg[4])
        self.id = int(msg[5])

    def update(self,msg):
        if isinstance(msg , bytes):
            msg = msg.decode()
        msg = msg.split(',')
        self.pos.x = int(msg[0])
        self.pos.y = int(msg[1])
        self.pos.width = int(msg[2])
        self.pos.height = int(msg[3])
        self.pos.speed = int(msg[4])
        self.pos.rotation = int(msg[5])

    def str(self):
        return self.pos.str()

if '__main__' == __name__:
    s = Server()
    s.wait_for_connection()