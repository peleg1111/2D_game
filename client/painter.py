__author__ = 'Peleg Etzioni'
import pygame, math , time, os , sys

sys.path.insert(0, os.path.dirname(__file__))# רשימת הקבצים שimport מחפש בהם קבצים להרצה
#  מכניס את התיקייה שבה נמצא הקובץ לרשימה כך שimport יוכל למצוא אותו ולהריץ מתוך הcmd

from const import *


class Painter:
    def __init__(self):
        # טוען תמונות
        self.player_img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()

        self.attack_img = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()

        self.background = pygame.image.load(IMAGE_ROOT + "background.png").convert_alpha()
        self.background = pygame.transform.scale(self.background, SCREEN_SIZE)

        self.wall_img = pygame.image.load(IMAGE_ROOT + "wall.png").convert_alpha()

        self.start_screen =pygame.image.load(IMAGE_ROOT + "start_screen.png").convert_alpha()
        self.start_screen = pygame.transform.scale(self.start_screen, SCREEN_SIZE)

        self.wait_screen = pygame.image.load(IMAGE_ROOT + "wait_screen.png").convert_alpha()
        self.wait_screen = pygame.transform.scale(self.wait_screen, SCREEN_SIZE)

        self.win_screen = pygame.image.load(IMAGE_ROOT + "win_screen.png").convert_alpha()
        self.win_screen = pygame.transform.scale(self.win_screen, SCREEN_SIZE)

        self.lose_screen = pygame.image.load(IMAGE_ROOT + "lose_screen.png").convert_alpha()
        self.lose_screen = pygame.transform.scale(self.lose_screen, SCREEN_SIZE)


    def draw_Background(self, screen):
        screen.blit(self.background, (0, 0))


    def draw_player(self, player):
        if not player:
            return
        rotated = pygame.transform.scale(self.player_img, (int(player.width * 2.6), int(player.height * 3)))
        rotated = pygame.transform.rotate(rotated, -player.rotation - 90)


        rect = rotated.get_rect(center=(player.x, player.y))

        player.screen.blit(rotated, rect)

        for i in range(player.hp):
            pygame.draw.rect(
                player.screen,
                (255, 0, 0),
                (player.x - player.width + i*8, player.y - player.height*2 + 20, 9, 7)
            )

    def draw_attack(self, attack):
        img = pygame.transform.scale(self.attack_img, (80 * (SCREEN_SIZE[1] / 650), 80 * (SCREEN_SIZE[1] / 650)))
        img = pygame.transform.rotate(img, -attack.rotation)

        rect = img.get_rect(center=(attack.x, attack.y))

        attack.screen.blit(img, rect)

    def draw_wall(self, wall):
        img_w, img_h = self.wall_img.get_size()
        cols = int(wall.width / img_w) + 1
        rows = int(wall.height / img_h) + 1

        for row in range(rows):
            for col in range(cols):
                x = wall.x + col * img_w
                y = wall.y + row * img_h
                cur_w = min(img_w, wall.x + wall.width - x)
                cur_h = min(img_h, wall.y + wall.height - y)
                wall.screen.blit(self.wall_img, (x, y), pygame.Rect(0, 0, cur_w, cur_h))


    def draw_waiting_screen(self, screen):
        screen.fill((30, 30, 30))
        screen.blit(self.wait_screen, (0, 0))
        font = pygame.font.SysFont(None, 70)
        text = font.render("waiting for another player" + (int(time.time())%3 + 1) * '.', True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))
        self.animation_dots(screen)


    def draw_lose_screen(self, screen):
        screen.fill((30, 30, 30))
        screen.blit(self.lose_screen, (0, 0))

        font = pygame.font.SysFont(None, 70)
        text = font.render("you lose", True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))
        self.animation_dots(screen)


    def draw_win_screen(self,screen):
        screen.fill((30, 30, 30))
        screen.blit(self.win_screen, (0, 0))
        font = pygame.font.SysFont(None, 70)
        text = font.render("you win", True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))

        self.animation_dots(screen)



    def draw_before_game_screen(self, screen):
        screen.fill((30, 30, 30))
        screen.blit(self.start_screen, (0, 0))
        font = pygame.font.SysFont(None, 70)
        text1 = font.render("PELEG'S GAME", True, (0, 0, 0))
        screen.blit(text1, (SCREEN_SIZE[0] // 2 - text1.get_width() // 2, SCREEN_SIZE[1] // 2 - SCREEN_SIZE[1] // 3))
        self.animation_dots(screen)


    def draw_disconnected_screen(self, screen):
        screen.fill((30, 30, 30))
        screen.blit(self.start_screen, (0, 0))
        font = pygame.font.SysFont(None, 70)
        text1 = font.render("disconnected", True, (0, 0, 0))
        screen.blit(text1, (SCREEN_SIZE[0] // 2 - text1.get_width() // 2, SCREEN_SIZE[1] // 2 - 160))
        self.animation_dots(screen)


    def draw_settings_screen(self, screen):
        screen.fill((30, 30, 30))
        font = pygame.font.SysFont(None, 70)
        text1 = font.render("settings", True, (255, 255, 255))
        screen.blit(text1, (SCREEN_SIZE[0] // 2 - text1.get_width() // 2, SCREEN_SIZE[1] // 2 - SCREEN_SIZE[1]/2.4))

        self.draw_credits(screen)


    def draw_credits(self, screen):
        font_title = pygame.font.SysFont(None, 45)
        font_text = pygame.font.SysFont(None, 30)

        lines = [
            ("=== Credits ===", font_title),
            ("", None),
            ("Game Design & Development", font_title),
            ("Peleg Etzioni", font_text),
            ("", None),
            ("Programming", font_title),
            ("Peleg Etzioni", font_text),
            ("", None),
            ("Art & Visual Design", font_title),
            ("Daniel Beserglick", font_text),
            ("", None),
            ("Music & Sound Effects", font_title),
            ("Peleg Etzioni", font_text),
            ("", None),
            ("Made with Python & Pygame", font_text),
            ("© 2025  Peleg Etzioni", font_text),
        ]

        y = SCREEN_SIZE[1] // 2 - 100
        for text, font in lines:
            if font is None:
                y += 10  # שורה ריקה
                continue
            surface = font.render(text, True, (222, 200, 23))
            x = SCREEN_SIZE[0] // 2 - surface.get_width() // 2
            screen.blit(surface, (x, y))
            y += surface.get_height() + 6


    def draw_encryption_screen(self, screen):

        screen.fill((30, 30, 30))
        screen.blit(self.start_screen, (0, 0))
        font = pygame.font.SysFont(None, 70)
        text1 = font.render("handle encryption" + (int(time.time())%3 + 1) * '.', True, (0, 0, 0))
        screen.blit(text1, (SCREEN_SIZE[0] // 2 - text1.get_width() // 2, SCREEN_SIZE[1] // 2 - 160))
        self.animation_dots(screen)


    def animation_dots(self, screen):
        t = time.time()
        radius = 20
        spacing = 70
        base_x = SCREEN_SIZE[0] // 2 - spacing
        y = SCREEN_SIZE[1] // 2 + 50


        for i in range(3):
            offset = math.sin(t * 3 + i) * 12
            pygame.draw.circle(screen, (13, 32, 245), (base_x + i * spacing, y + offset), radius)

        y2 = SCREEN_SIZE[0] * 0.08
        base_x2 = SCREEN_SIZE[0] // 5 - spacing
        y3 = SCREEN_SIZE[0] * 0.93

        for i in range(7):
            offset = math.sin(t * 3 + i) * 7
            pygame.draw.circle(screen, (245, 221, 19), (y2 + offset, base_x2 + i * spacing), radius)
            pygame.draw.circle(screen, (245, 221, 19), (y3 + offset, base_x2 + i * spacing), radius)

