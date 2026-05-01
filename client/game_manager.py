import time

import pygame, threading
from enum import Enum
from const import *
from painter import Painter
from Button import Button

class GameState(Enum):
    WIN = -1
    LOSE = 0
    BEFORE_GAME = 1
    WAITING = 2
    PLAYING = 3

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
        self.player = None
        self.players = []
        self.attacks = []
        self.game_state = GameState.BEFORE_GAME
        self.lock = threading.Lock()
        self.walls = self.create_maze_walls()
        self.start_timer_screen = None
        self.start_game_button = Button(
            SCREEN_SIZE[0]/2 - 50 , 220 , 100 , 65 ,"   play   ",
            pygame.font.SysFont("Arial", 50),(100,100,100), (50,60,70)
        )

        self.exit_button = Button(
            0 ,0 , 100 , 65 ,"exit",
            pygame.font.SysFont("Arial", 50),(100,100,100), (50,60,70)
        )
    def create_maze_walls(self):
        walls = []
        W, H = SCREEN_SIZE

        # גבולות חיצוניים
        walls.append(Wall(self.screen,0, 0, W, WALL_SIZE))
        walls.append(Wall(self.screen,0, H - WALL_SIZE, W, WALL_SIZE))
        walls.append(Wall(self.screen,0, 0, WALL_SIZE, H))
        walls.append(Wall(self.screen,W - WALL_SIZE, 0, WALL_SIZE, H))
        #קירות המבוך
        walls.append(Wall(self.screen,W * 0.1, H * 0.45, W * 0.8, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.48, H * 0.1, WALL_SIZE, H * 0.8))
        walls.append(Wall(self.screen,W * 0.1, H * 0.1, W * 0.25, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.1, H * 0.1, WALL_SIZE, H * 0.25))
        walls.append(Wall(self.screen,W * 0.65, H * 0.1, W * 0.25, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.9 - WALL_SIZE, H * 0.1, WALL_SIZE, H * 0.25))
        walls.append(Wall(self.screen,W * 0.25, H * 0.25, W * 0.15, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.6, H * 0.25, W * 0.15, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.1, H * 0.65, W * 0.25, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.1, H * 0.65, WALL_SIZE, H * 0.25))
        walls.append(Wall(self.screen,W * 0.65, H * 0.65, W * 0.25, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.9 - WALL_SIZE, H * 0.65, WALL_SIZE, H * 0.25))
        walls.append(Wall(self.screen,W * 0.25, H * 0.55, W * 0.15, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.6, H * 0.55, W * 0.15, WALL_SIZE))
        walls.append(Wall(self.screen,W * 0.45, H * 0.45, W * 0.1, WALL_SIZE))

        return walls


    def create_screen(self):
        pygame.init()
        screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption(SCREEN_NAME)
        return screen


    def clean_screen(self):
        self.screen.fill(SCREEN_COLOR)


    def update_screen(self):
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

        if self.game_state == GameState.WAITING:
            self.painter.draw_waiting_screen(self.screen)


        elif self.game_state == GameState.LOSE:
            self.painter.draw_lose_screen(self.screen)
            now = time.time()

            if not self.start_timer_screen:
                self.start_timer_screen = time.time()

            if now - self.start_timer_screen > TIME_BETWEEN_STATES:
                self.start_timer_screen = None
                self.game_state = GameState.BEFORE_GAME


        elif self.game_state == GameState.BEFORE_GAME:
            self.painter.draw_before_game_screen(self.screen)
            self.start_game_button.draw(self.screen)
            self.exit_button.draw(self.screen)


        elif self.game_state == GameState.WIN:
            self.painter.draw_win_screen(self.screen)
            now = time.time()

            if not self.start_timer_screen:
                self.start_timer_screen = time.time()

            if now - self.start_timer_screen > TIME_BETWEEN_STATES:
                self.start_timer_screen = None
                self.game_state = GameState.BEFORE_GAME


        else:   self.update_screen()

        pygame.display.flip()

    def update_from_server(self, msg):
        # STATE|PLAYER,...|ATTACK,...|
        parts = msg.split("|")[1:]

        with self.lock:
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