import pygame, math
from const import *

class Painter:
    def __init__(self):
        # טוען תמונות
        self.player_img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()
        self.attack_img = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()
        self.background = pygame.image.load(IMAGE_ROOT + "background.png").convert_alpha()
        self.background = pygame.transform.scale(self.background, SCREEN_SIZE)

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
        rotated = pygame.transform.rotate(self.attack_img, -attack.rotation)

        rotated = pygame.transform.scale(rotated, (80, 80))

        rect = rotated.get_rect(center=(attack.x, attack.y))

        attack.screen.blit(rotated, rect)

    def draw_wall(self, wall):
        pygame.draw.rect(wall.screen, (255, 255, 255), wall.hitbox)


    def draw_waiting_screen(self, screen):
        screen.fill(SCREEN_COLOR)
        font = pygame.font.SysFont(None, 50)
        text = font.render("waiting for another player...", True, (255, 255, 255))
        screen.blit(text, (190, 200))
        pygame.display.flip()
