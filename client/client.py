import random , time , socket , threading , pygame
from const import *
from game_manager import GameManager, GameState

class Client:
    def __init__(self):
        self.dst = ADDR_SERVER
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manager = GameManager(self)
        self.run = True
        self.lock = threading.Lock()
        threading.Thread(target=self.recv, daemon=True).start()

    def send_msg(self, msg):
        self.sock.sendto( msg.encode() if isinstance(msg, str) else msg , self.dst)
        print(f'sent to server -->> {len(msg)}|{msg}')


    def main_loop(self):
        clock = pygame.time.Clock()

        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    return
            keys = pygame.key.get_pressed()

            if self.manager.game_state != GameState.PLAYING:
                if keys[pygame.K_SPACE] and self.manager.game_state == GameState.BEFORE_GAME:
                    self.start()
                self.manager.main_loop()
                continue

            key = ""
            if keys[pygame.K_w]: key += "W"
            if keys[pygame.K_s]: key += "S"
            if keys[pygame.K_a]: key += "A"
            if keys[pygame.K_d]: key += "D"
            if keys[pygame.K_SPACE]: key += "!"

            if key == "":
                key = 'None'

            self.send_msg(f"INPUT|{key}")
            self.manager.main_loop()
            clock.tick(FPS)


    def handle_msg(self, msg):
        if msg.startswith("STATE"):
            self.manager.game_state = GameState.PLAYING
            self.manager.update_from_server(msg)

        elif msg == LOSE_GAME.decode():
            self.manager.game_state = GameState.LOSE

        elif msg == WAIT.decode() and self.manager.game_state != GameState.PLAYING:
            self.manager.game_state = GameState.WAITING

        elif msg == WIN_GAME.decode():
            self.manager.game_state = GameState.WIN

    def start(self):
        self.sock.sendto(START_GAME, self.dst)
        self.game_state = GameState.WAITING

    def recv(self):
        while self.run:
            try:
                data, addr = self.sock.recvfrom(2048)
                msg = data.decode()
                print(f"got from server -->> {len(data)}|{msg}")
                self.handle_msg(msg)
            except socket.error:
                continue


def main():
    client = Client()
    client.main_loop()


if __name__ == "__main__":
    main()
