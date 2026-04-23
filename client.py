import random
import socket , sys
import threading
from const import *
from const_class import *


class Client:
    def __init__(self):
        self.dst = ADDR_SERVER
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manager = self.manager_init()
        self.run = True
        self.lock = threading.Lock()


        threading.Thread(target=self.recv).start()



    def manager_init(self):
        manager = GameManager()
        manager.game_state = GameState.WAITING
        t = Tank(manager.screen, random.randint(50 , 600), random.randint(50 , 600), 25, 25, (0, 255, 0), 0.1, 1000, 4)
        manager.Add_player(t)
        return manager

    def main_loop(self):
        self.sock.sendto(START_GAME, ADDR_SERVER)

        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    return
            self.manager.main_loop()
            if self.manager.game_state == GameState.PLAYING:
                data = self.manager.str()
                for i in data:
                    self.sock.sendto(i.encode(), ADDR_SERVER)

    def handle_msg(self, msg):
        with self.lock:
            if msg.startswith(INFO):
                self.manager.game_state = GameState.PLAYING
                self.manager.update_other_players_and_attacks(msg)


            elif msg.startswith(END_GAME):
                self.manager.game_state = GameState.WAITING


    def recv(self):
        while self.run:
            self.sock.settimeout(2)
            try:
                with self.lock:
                    data, addr = self.sock.recvfrom(2048)

                print('Got data:', data.decode())
                self.handle_msg(data)
            except socket.error:
                self.sock.settimeout(None)



def main():
    client = Client()
    client.main_loop()


if __name__ == "__main__":
    main()