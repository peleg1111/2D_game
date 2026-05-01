import pygame, math , time
from const import *

class Painter:
    def __init__(self):
        # טוען תמונות
        self.player_img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()
        self.attack_img = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()
        self.background = pygame.image.load(IMAGE_ROOT + "background.png").convert_alpha()
        self.background = pygame.transform.scale(self.background, SCREEN_SIZE)
        self.wall_img = pygame.image.load(IMAGE_ROOT + "wall.png").convert_alpha()

    def draw_Background(self, screen):
        screen.blit(self.background, (0, 0))


    def draw_player(self, player):
        if not player:
            return
        rotated = pygame.transform.scale(self.player_img, (int(player.width*3), int(player.height*3)))
        rotated = pygame.transform.rotate(rotated, -player.rotation - 90)


        rect = rotated.get_rect(center=(player.x, player.y))

        player.screen.blit(rotated, rect)

        for i in range(player.hp):
            pygame.draw.rect(
                player.screen,
                (255, 0, 0),
                (player.x - player.width + i*8, player.y - player.height*2 + 20, 6, 6)
            )

    def draw_attack(self, attack):
        rotated = pygame.transform.scale(self.attack_img, (80, 80))
        rotated = pygame.transform.rotate(rotated, -attack.rotation)


        rect = rotated.get_rect(center=(attack.x, attack.y))

        attack.screen.blit(rotated, rect)

    def draw_wall(self, wall):
        img = pygame.transform.scale(self.wall_img, (wall.width, wall.height))
        wall.screen.blit(img, (wall.x , wall.y))



    def draw_waiting_screen(self, screen):
        screen.fill((30, 30, 30))

        font = pygame.font.SysFont(None, 70)
        text = font.render("waiting for another player", True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))
        self.animation_3dot(screen)

    def draw_lose_screen(self, screen):
        screen.fill((30, 30, 30))

        font = pygame.font.SysFont(None, 70)
        text = font.render("you lose", True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))
        self.animation_3dot(screen)


    def draw_win_screen(self,screen):
        screen.fill((30, 30, 30))

        font = pygame.font.SysFont(None, 70)
        text = font.render("you win", True, (255, 255, 255))
        screen.blit(text, (SCREEN_SIZE[0] // 2 - text.get_width() // 2, SCREEN_SIZE[1] // 2 - 120))

        self.animation_3dot(screen)




    def draw_before_game_screen(self, screen):
        screen.fill((30, 30, 30))
        font = pygame.font.SysFont(None, 70)
        text1 = font.render("PELEG'S GAME", True, (255, 255, 255))
        screen.blit(text1, (SCREEN_SIZE[0] // 2 - text1.get_width() // 2, SCREEN_SIZE[1] // 2 - 160))
        self.animation_3dot(screen)


    def animation_3dot(self, screen):
        t = time.time()
        radius = 12
        spacing = 40
        base_x = SCREEN_SIZE[0] // 2 - spacing
        y = SCREEN_SIZE[1] // 2 + 50

        for i in range(3):
            offset = math.sin(t * 3 + i) * 12
            pygame.draw.circle(screen, (255, 255, 255), (base_x + i * spacing, y + offset), radius)