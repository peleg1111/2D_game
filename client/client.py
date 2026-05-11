import socket , threading , pygame , time
from const import *
from game_manager import GameManager, GameState
from audio import Audio

class Client:
    def __init__(self):
        self.dst = ADDR_SERVER
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.manager = GameManager(self)
        self.run = True
        self.lock = threading.Lock()
        threading.Thread(target=self.recv, daemon=True).start()
        self.audio = Audio()


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
                    self.send(WAIT)

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
            self.manager.update_from_server(msg)

        elif msg == LOSE_GAME.decode():
            self.manager.game_state = GameState.LOSE
            self.audio.play_lose_song()

        elif msg == WIN_GAME.decode():
            self.manager.game_state = GameState.WIN
            self.audio.play_win_song()

        elif msg.startswith(AUDIO.decode()):
            if msg.split("|")[1] == str(audio_type.HIT_WALL):
                self.audio.play_hit_wall_song()
                self.audio.play_hit_wall_song()


            elif msg.split("|")[1] == str(audio_type.HIT_PLAYER):
                self.audio.play_hit_player_song()


    def start(self):
        self.send(START_GAME)
        self.manager.game_state = GameState.WAITING


    def recv(self):
        while self.run:
            if self.manager.game_state != GameState.WAITING and self.manager.game_state != GameState.PLAYING:
                self.Wait()
            else:
                self._recv()


    def Wait(self):
        time.sleep(0.2)


    def _recv(self):
        try:
            self.sock.settimeout(TIME_BEFORE_REMOVE)
            data, addr = self.sock.recvfrom(2048)
            msg = data.decode()
            print(f"got from server -->> {len(data)}|{msg}")
            self.handle_msg(msg)
        except socket.error as e:
            print(e)
            self.sock.settimeout(None)
            self.manager.game_state = GameState.DISCONNECTED


    def send(self, msg):
        self.sock.sendto(msg.encode() if isinstance(msg , str) else msg, self.dst)
        print("send to server --> ",msg)


    def is_clicked(self, button, event):
        if button.is_clicked(event):
            self.audio.play_click()
            time.sleep(0.5)
            return True
        return False

def main():
    client = Client()
    client.main_loop()


if __name__ == "__main__":
    main()