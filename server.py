from const import *
from const_class import *
import socket, threading

class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 1234))

        self.players = {}   # id : addr
        self.rooms = []
        self.next_ID = 0

    def recv(self):
        while True:
            data, addr = self.socket.recvfrom(1024)

            # השחקן מבקש להצטרף למשחק
            if data == START_GAME:
                player_id = self.next_ID
                self.players[player_id] = addr
                self.next_ID += 1

                self.socket.sendto(ACK, addr)

                # חיפוש חדר עם שחקן אחד
                for room in self.rooms:
                    if room.num_of_players == 1:
                        room.add_player(player_id, addr)
                        return

                # אם אין חדר פנוי יוצרים חדר חדש
                room = Room(self.socket)
                room.add_player(player_id, addr)
                self.rooms.append(room)
                room.start()
                print(f"new client {addr = }")

            else:
                # מציאת השחקן לפי כתובת
                player_id = None
                for pid, paddr in self.players.items():
                    if paddr == addr:
                        player_id = pid
                        break

                if player_id is None:
                    continue

                # שליחת הפקודה לחדר הנכון
                for room in self.rooms:
                    if player_id in room.players:
                        room.handler(data, player_id)
                        break


class Room(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket
        self.players = {}  # id : addr
        self.num_of_players = 0
        self.cmd_queue = {}  # id : last_cmd

    def add_player(self, player_id, addr):
        self.players[player_id] = addr
        self.num_of_players += 1

    def handler(self, data, player_id):
        self.cmd_queue[player_id] = data

    def run(self):
        self.game_manager = GameManager()

        # יצירת טנקים לפי מספר השחקנים
        for i in self.players:
            t = Tank(self.game_manager.screen, 300, 400, 25, 25, (0,255,0), 0.1, 2000)
            self.game_manager.Add_player(t, i)

        while True:
            for id, cmd in list(self.cmd_queue.items()):
                self.game_manager.main_loop(id, cmd)
                del self.cmd_queue[id]

            self.game_manager.main_loop(None)



if __name__ == "__main__":
    s = Server()
    s.recv()



