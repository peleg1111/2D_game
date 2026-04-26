import pygame, threading
from enum import Enum
from const import *
from painter import Painter

class GameState(Enum):
    BEFORE_GAME = 1
    WAITING = 2
    PLAYING = 3

class Wall:
    def __init__(self, screen, x, y, size_x, size_y):
        self.hitbox = pygame.Rect(x, y, size_x, size_y)
        self.screen = screen


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
    def __init__(self):
        self.screen = self.create_screen()
        self.painter = Painter()
        self.player = None
        self.other_players = []
        self.attacks = []
        self.game_state = GameState.WAITING
        self.lock = threading.Lock()

        self.walls = self.create_maze_walls()

    def create_maze_walls(self):
        walls = []
        T = 12  # עובי קיר
        W, H = SCREEN_SIZE

        # גבולות חיצוניים
        walls.append(Wall(self.screen,0, 0, W, T))
        walls.append(Wall(self.screen,0, H - T, W, T))
        walls.append(Wall(self.screen,0, 0, T, H))
        walls.append(Wall(self.screen,W - T, 0, T, H))
        #קירות המבוך
        walls.append(Wall(self.screen,W * 0.1, H * 0.45, W * 0.8, T))
        walls.append(Wall(self.screen,W * 0.48, H * 0.1, T, H * 0.8))
        walls.append(Wall(self.screen,W * 0.1, H * 0.1, W * 0.25, T))
        walls.append(Wall(self.screen,W * 0.1, H * 0.1, T, H * 0.25))
        walls.append(Wall(self.screen,W * 0.65, H * 0.1, W * 0.25, T))
        walls.append(Wall(self.screen,W * 0.9 - T, H * 0.1, T, H * 0.25))
        walls.append(Wall(self.screen,W * 0.25, H * 0.25, W * 0.15, T))
        walls.append(Wall(self.screen,W * 0.6, H * 0.25, W * 0.15, T))
        walls.append(Wall(self.screen,W * 0.1, H * 0.65, W * 0.25, T))
        walls.append(Wall(self.screen,W * 0.1, H * 0.65, T, H * 0.25))
        walls.append(Wall(self.screen,W * 0.65, H * 0.65, W * 0.25, T))
        walls.append(Wall(self.screen,W * 0.9 - T, H * 0.65, T, H * 0.25))
        walls.append(Wall(self.screen,W * 0.25, H * 0.55, W * 0.15, T))
        walls.append(Wall(self.screen,W * 0.6, H * 0.55, W * 0.15, T))
        walls.append(Wall(self.screen,W * 0.45, H * 0.45, W * 0.1, T))

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
            if self.player:
                self.painter.draw_player(self.player)

            for p in self.other_players:
                self.painter.draw_player(p)

            for atk in self.attacks:
                self.painter.draw_attack(atk)

        pygame.display.flip()

    def main_loop(self):
        self.clean_screen()
        if self.game_state == GameState.WAITING:
            self.painter.draw_waiting_screen(self.screen)
        else:
            self.update_screen()

    def update_from_server(self, msg):
        # STATE|PLAYER,...|ATTACK,...|
        parts = msg.split("|")[1:]

        with self.lock:
            self.other_players = []
            self.attacks = []
            local_set = False

            for part in parts:
                if part.startswith("PLAYER"):
                    _, x, y, w, h, hp, rot = part.split(",")
                    x = float(x); y = float(y)
                    w = float(w); h = float(h)
                    hp = int(hp); rot = float(rot)

                    if not local_set:
                        self.player = TankClient(self.screen, x, y, w, h, rot, hp)
                        local_set = True
                    else:
                        self.other_players.append(
                            TankClient(self.screen, x, y, w, h, rot, hp)
                        )

                elif part.startswith("ATTACK"):
                    _, x, y, rot = part.split(",")
                    x = float(x); y = float(y); rot = float(rot)
                    self.attacks.append(AttackClient(self.screen, x, y, rot))
