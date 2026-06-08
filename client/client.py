__author__ = 'Peleg Etzioni'
import socket , threading , pygame , time , random , sys

from const import *
from game_manager import GameManager, GameState
from audio import Audio
from encryption.encryption_manager import *
from encryption_client import ClientHandshake

class Client:
    def __init__(self,ip , port):
        self.dst = (ip,port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manager = GameManager(self)
        self.run = True
        self.lock = threading.Lock()
        self.aes = None
        threading.Thread(target=self.do_handshake, daemon=True).start()
        threading.Thread(target=self.recv, daemon=True).start()
        self.audio = Audio()
        self.last_seq_num = 0
        self.ack_received = []


    def do_handshake(self):
        self.manager.game_state = GameState.ENCRYPTION
        while self.aes is None:
            hs = ClientHandshake(self.sock, self.dst)
            self.aes = hs.run()
            if self.aes is None:
                print("Client --> encryption handshake failed")

        self.manager.game_state = GameState.BEFORE_GAME
        print("Client --> AES key")


    def main_loop(self):
        clock = pygame.time.Clock()
        self.audio.play_background_song()

        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    return

                elif self.manager.game_state == GameState.BEFORE_GAME:
                    if self.is_clicked(self.manager.start_game_button, event):
                        self.start()

                    if self.is_clicked(self.manager.exit_button, event):
                        self.run = False
                        return

                    if self.is_clicked(self.manager.settings_button, event):
                        self.manager.game_state = GameState.SETTINGS

                elif self.manager.game_state == GameState.SETTINGS:

                    if self.is_clicked(self.manager.back_to_menu_button, event):
                        self.manager.game_state = GameState.BEFORE_GAME

                    self.manager.volume_slider.handle_event(event)

                    if self.manager.volume_slider.is_dragging():
                        self.audio.set_all(self.manager.volume_slider.val)

            keys = pygame.key.get_pressed()

            if self.manager.game_state != GameState.PLAYING:

                if self.manager.game_state == GameState.WAITING:
                    self.send(START_GAME)


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

            self.send(f"INPUT|{key}")
            self.manager.main_loop()
            clock.tick(FPS)


    def handle_msg(self, msg):
        if msg.startswith("STATE"):
            self.manager.game_state = GameState.PLAYING
            seq_num = int(msg.split("|")[0].replace("STATE",""))
            if seq_num < self.last_seq_num:
                return
            self.last_seq_num = seq_num
            self.manager.update_from_server(msg)

        elif msg == LOSE_GAME.decode():
            self.manager.game_state = GameState.LOSE
            self.audio.play_lose_song()

        elif msg == WIN_GAME.decode():
            self.manager.game_state = GameState.WIN
            self.audio.play_win_song()

        elif msg.startswith(WALLS.decode()):
            with self.lock:
                self.manager.walls = self.manager.create_maze_walls( int( msg.split('|') [1] ) )
                self.send('ACK|'+ WALLS.decode())



    def start(self):
        self.send(START_GAME)
        self.manager.game_state = GameState.WAITING


    def recv(self):
        while self.run:
            if self.manager.game_state == GameState.WAITING or self.manager.game_state == GameState.PLAYING:
                self._recv()

            elif self.manager.game_state == GameState.ENCRYPTION:
                pass

            else:
                self._clean_buffer()


    def _clean_buffer(self):
        try:
            self.sock.settimeout(0.3)
            self.send(WAIT)  # כדי שהשרת ידע שהלקוח מחובר גם לאחר ההתחברות
            data, addr = self.sock.recvfrom(2048)

        except socket.error as e:
            self.sock.settimeout(None)

    def _recv(self):
        try:
            self.sock.settimeout(TIME_BEFORE_REMOVE)
            data, addr = self.sock.recvfrom(4096)

            if self.aes:
                try:
                    data = self.aes.decrypt(data)
                except Exception:
                    return

            msg = data.decode()
            print(f"got from server -->> {len(msg)}|{msg}")
            self.handle_msg(msg)

        except socket.error as e:
            print(e)
            self.sock.settimeout(None)
            self.manager.game_state = GameState.DISCONNECTED


    def send(self, msg, DROP_RATE=0.1, CHANGE_RATE=0.14):
        msg = msg.encode() if isinstance(msg, str) else msg

        num = random.random()
        if num < DROP_RATE:
            print(f"msg lost --> {msg}")
            return
        if num < CHANGE_RATE:

            if not self.aes:
                arr = list(msg.decode())
                random.shuffle(arr)
                msg = "".join(arr).encode()
                print(f"\n\nmsg changed --> {msg}\n\n")

        print("send to server --> ", msg)
        if self.aes:
            msg = self.aes.encrypt(msg)

        if DEBUG:
            print(f"encrypted msg --> {msg}\n\n")

        self.sock.sendto(msg, self.dst)



    def is_clicked(self, button, event):
        if button.is_clicked(event):
            self.audio.play_click()
            time.sleep(0.5)
            return True
        return False


def main():

    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    else:
        ip,port = ADDR_SERVER

    client = Client(ip,port)
    client.main_loop()


if __name__ == "__main__":
    main()