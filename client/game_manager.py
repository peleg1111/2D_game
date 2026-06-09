__author__ = 'Peleg Etzioni'
import pygame, threading , time, os , sys

sys.path.insert(0, os.path.dirname(__file__))# רשימת הקבצים שimport מחפש בהם קבצים להרצה
#  מכניס את התיקייה שבה נמצא הקובץ לרשימה כך שimport יוכל למצוא אותו ולהריץ מתוך הcmd

from const import *
from painter import Painter
from Button import Button
from Slider import Slider


class GameState(Enum):
    WIN = 0
    LOSE = 1
    BEFORE_GAME = 2
    WAITING = 3
    PLAYING = 4
    DISCONNECTED = 5
    SETTINGS = 6
    ENCRYPTION = 7

class Wall:
    def __init__(self, screen, x, y, width, height):
        self.hitbox = pygame.Rect(x, y, width, height)
        self.screen = screen
        self.width = width
        self.height = height
        self.x = x
        self.y = y


class TankClient:
    def __init__(self, screen, x, y, width, height, rotation, hp):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.hp = hp
        self.hitbox = pygame.Rect(0, 0, width, height)
        self.hitbox.center = (self.x, self.y)


class AttackClient:
    def __init__(self, screen, x, y, rotation):
        self.screen = screen
        self.x = x
        self.y = y
        self.rotation = rotation


class GameManager:
    def __init__(self, client):
        self.client = client
        self.screen = self.create_screen()
        self.painter = Painter()
        self.players = [] # Tank
        self.attacks = []
        self.game_state = GameState.ENCRYPTION
        self.lock = threading.Lock()
        self.walls = None
        self.start_timer_screen = None
        
        self.start_game_button = Button(
            SCREEN_SIZE[0]/2 - 50 , SCREEN_SIZE[1]/3 , 100 , 65 ,"   play   ",
            pygame.font.SysFont("Arial", 50),(100,100,100), (50,60,70)
        )

        self.exit_button = Button(
            0 ,0 , 100 , 65 ,"exit",
            pygame.font.SysFont("Arial", 50),(100,100,100), (50,60,70)
        )

        self.settings_button = Button(
            SCREEN_SIZE[0]-150, 0, 150, 65, "settings",
            pygame.font.SysFont("Arial", 50), (100, 100, 100), (50, 60, 70)
        )

        self.back_to_menu_button = Button(
            0, 0, 100, 65, "back",
            pygame.font.SysFont("Arial", 50), (100, 100, 100), (50, 60, 70)
        )

        self.volume_slider = Slider(
            SCREEN_SIZE[0]/3, SCREEN_SIZE[1]/5, 300, 0,
            2.5,1 , 'volume:'
        )

    def create_maze_walls(self, maze_num):

        maze = ALL_MAZES.get(maze_num, MAZE_1)
        return [
            Wall(self.screen, x, y, width, height) for x, y, width, height in maze
        ]


    def create_screen(self):
        pygame.init()
        screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption(SCREEN_NAME)
        return screen


    def clean_screen(self):
        self.screen.fill(SCREEN_COLOR)


    def update_screen(self):

        ttl = time.time() + TIME_BEFORE_REMOVE
        while self.walls is None and time.time() < ttl :
            time.sleep(0.1)

        if self.walls is None:
            self.game_state = GameState.DISCONNECTED
            return

        self.painter.draw_Background(self.screen)

        for wall in self.walls:
            self.painter.draw_wall(wall)

        with self.lock:
            for p in self.players:
                self.painter.draw_player(p)

            for atk in self.attacks:
                self.painter.draw_attack(atk)


    def main_loop(self):
        self.clean_screen()
        match self.game_state:

            case GameState.WAITING:
                self.painter.draw_waiting_screen(self.screen)
                self.players = []
                self.attacks = []
                self.client.last_seq_num = 0



            case GameState.LOSE:
                self.painter.draw_lose_screen(self.screen)
                now = time.time()

                if not self.start_timer_screen:
                    self.start_timer_screen = time.time()

                if now - self.start_timer_screen > TIME_BETWEEN_STATES:
                    self.start_timer_screen = None
                    self.game_state = GameState.BEFORE_GAME


            case GameState.BEFORE_GAME:
                self.painter.draw_before_game_screen(self.screen)
                self.start_game_button.draw(self.screen)
                self.exit_button.draw(self.screen)
                self.settings_button.draw(self.screen)


            case GameState.WIN:
                self.painter.draw_win_screen(self.screen)
                now = time.time()

                if not self.start_timer_screen:
                    self.start_timer_screen = time.time()

                if now - self.start_timer_screen > TIME_BETWEEN_STATES:
                    self.start_timer_screen = None
                    self.game_state = GameState.BEFORE_GAME


            case GameState.PLAYING:
                self.update_screen()


            case GameState.DISCONNECTED:
                self.painter.draw_disconnected_screen(self.screen)
                now = time.time()

                if not self.start_timer_screen:
                    self.start_timer_screen = time.time()

                if now - self.start_timer_screen > TIME_BETWEEN_STATES:
                    self.start_timer_screen = None
                    self.game_state = GameState.BEFORE_GAME

            case GameState.SETTINGS:
                self.painter.draw_settings_screen(self.screen)
                self.back_to_menu_button.draw(self.screen)
                self.volume_slider.draw(self.screen)

            case GameState.ENCRYPTION:
                self.painter.draw_encryption_screen(self.screen)
        pygame.display.flip()

    def update_from_server(self, msg):
        # STATE|PLAYER,...|ATTACK,...|
        parts = msg.split("|")[1:]

        with self.lock:

            hp_arr = [
                i.hp for i in self.players
            ]
            hp_arr.sort()

            rotations = [
                i.rotation for i in self.attacks
            ]

            self.players = []
            self.attacks = []




            for part in parts:
                if part.startswith("PLAYER"):
                    _, x, y, w, h, hp, rot = part.split(",")
                    x = float(x); y = float(y)
                    w = float(w); h = float(h)
                    hp = int(hp); rot = float(rot)

                    self.players.append(
                        TankClient(self.screen, x, y, w, h, rot, hp)
                    )

                elif part.startswith("ATTACK"):
                    _, x, y, rot = part.split(",")
                    x = float(x); y = float(y); rot = float(rot)
                    self.attacks.append(AttackClient(self.screen, x, y, rot))

            _hp_arr = [
                i.hp for i in self.players
            ]
            _hp_arr.sort()

            if len(_hp_arr) != len(hp_arr):
                self.client.audio.play_hit_player_song()

            else:
                for i in range(len(_hp_arr)):
                    if _hp_arr[i] != hp_arr[i]:
                        self.client.audio.play_hit_player_song()
                        return
            _rotations = [
                i.rotation for i in self.attacks
            ]
            if len(_rotations) != len(rotations):
                self.client.audio.play_hit_wall_song()
            for i in range(len(_rotations)):
                if not _rotations[i] in rotations:
                    self.client.audio.play_hit_wall_song()
