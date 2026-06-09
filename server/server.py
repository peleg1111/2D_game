__author__ = 'Peleg Etzioni'
import socket, threading, time, random, pygame, math, os , sys

sys.path.insert(0, os.path.dirname(__file__))# רשימת הקבצים שimport מחפש בהם קבצים להרצה
#  מכניס את התיקייה שבה נמצא הקובץ לרשימה כך שimport יוכל למצוא אותו ולהריץ מתוך הcmd

from const import *
from encryption_server import Server_encryption
from server_UI import Server_ui
from server_room import Room



class Server:
    def __init__(self, max_player_in_room=PLAYER_COUNT):
        self.sock = self.create_sock()
        self.rooms = []
        self.lock = threading.Lock()
        self.clients = [] # addr
        self.max_players_in_room = max_player_in_room
        self.active = True
        self.aes = {} # addr --> AESManager
        self.timer = {}# addr --> Time
        self.encryption_manager = Server_encryption(
            self.sock, self.aes, self.lock
        )


    def create_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 1234))
        sock.settimeout(2)
        print("server started on port 1234")
        return sock


    def start(self):
        threading.Thread(target=self.clean_dead_rooms, daemon=True).start()
        self.remove_dead_players()

        while self.active:
            data, addr = self.recv()
            if not addr or not data:
                continue

            if self.encryption_manager.handle(data, addr):
                continue

            if addr not in self.aes:
                print(f"server ignoring unencrypted msg from {addr}")
                self.send(NOT_ENCRYPTED,addr)
                continue

            self.register(addr, data)

            if data == START_GAME and not self.find_room(addr):
                self.join_room(addr)
            else:
                room = self.find_room(addr)
                if room:
                    room.handle_input(addr, data)


    def send(self,msg , addr,DROP_RATE = 0.1, CHANGE_RATE = 0.14):
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

        if not self.aes.get(addr, None) is None:
            msg = self.server.aes[addr].encrypt(msg)

        self.sock.sendto(msg,addr)


    def remove_dead_players(self):
        threading.Thread(target=self._remove_dead_players, daemon=True).start()


    def _remove_dead_players(self):
        while True:
            with self.lock:
                for i in self.clients[:]:
                    found = any(i in room.players for room in self.rooms)
                    if not found:
                        self.clients.remove(i)
                for addr , _time in list(self.timer.items()):
                    if time.time() > _time + 5:
                        del self.timer[addr]
                        if self.aes.get(addr, None) is not None:
                            del self.aes[addr]
                            print(f"dead players removed from {addr}")

            time.sleep(0.5)


    def recv(self):
        try:
            data, addr = self.sock.recvfrom(2048 * 4)

            is_hand_shake = False
            for i in (ENC_HELLO, ENC_PARAMS, ENC_PUBKEY, ENC_DONE):
                if data.startswith(i):
                    is_hand_shake = True

            if not is_hand_shake:
                aes = self.aes.get(addr, None)
                if aes:
                    try:
                        data = aes.decrypt(data)
                    except Exception:
                        return (None, None)

            print(f"got from {addr} -->> {len(data)}|" + data.decode(errors='replace'))
            return (data, addr)

        except socket.timeout:
            return (None, None)
        except Exception as e:
            print(e)
            return (None, None)


    def register(self, addr, data):
        with self.lock:
            if addr not in self.clients and data != WAIT:
                self.clients.append(addr)
            self.timer[addr] = time.time()


    def clean_dead_rooms(self):
        while True:
            with self.lock:
                for i in self.rooms[:]:
                    if not i.running:
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


    def State(self):
        state = ""
        for num, i in enumerate(self.rooms):
            state += (f"\n       room{num + 1}        \n"
                      f"players count: {i.player_count}\n"
                      f"attacks count: {len(i.attacks)}\n")
        return (f"=========  SERVER  ============\n"
                f"default players count in each room: {self.max_players_in_room}\n"
                f"room count: {len(self.rooms)}\n"
                f"players in server(in total): {len(self.clients)}\n"
                f"encrypted clients: {len(self.aes)}\n"
                f"=================================\n"
                f"{state}\n")


def main():
    server = Server()
    server_ui = Server_ui(server)
    t = threading.Thread(target=server.start, daemon=True)
    t.start()
    server_ui.mainloop()
    t.join()


if __name__ == "__main__":
    main()