import random

import pygame, math , time
from const import *

class Tank:
    def __init__(self, x, y, width, height, speed, hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.rotation = 0
        self.hp = hp
        self.last_attack = time.time()
        self.cooldown = 1

    def move(self, direction, walls, other_players):
        old_x = self.x
        old_y = self.y
        rad = math.radians(self.rotation)

        self.x += math.cos(rad) * self.speed * direction
        rect = self.get_rect()

        for wall in walls:
            if rect.colliderect(wall.hitbox):
                self.x = old_x
                rect = self.get_rect()

        for p in other_players:
            if rect.colliderect(p.get_rect()):
                self.x = old_x
                rect = self.get_rect()

        self.y += math.sin(rad) * self.speed * direction
        rect = self.get_rect()

        for wall in walls:
            if rect.colliderect(wall.hitbox):
                self.y = old_y
                rect = self.get_rect()

        for p in other_players:
            if rect.colliderect(p.get_rect()):
                self.y = old_y
                rect = self.get_rect()

    def rotate(self, delta):
        self.rotation += delta

    def get_rect(self):
        return pygame.Rect(self.x - self.width/2,
                           self.y - self.height/2,
                           self.width,
                           self.height)

    def is_hit_by(self, atk):
        rect = self.get_rect()
        return rect.collidepoint(atk.x, atk.y)


class Attack:
    def __init__(self, x, y, rotation, speed=4):
        rad = math.radians(rotation)
        self.x = x + math.cos(rad) * 15
        self.y = y + math.sin(rad) * 15
        self.rotation = rotation
        self.speed = speed
        self.bounss = 7

    def update(self, walls, players):
        old_x = self.x
        old_y = self.y

        rad = math.radians(self.rotation)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        rect = pygame.Rect(self.x - 3, self.y - 3, 6, 6)

        for wall in walls:
            if rect.colliderect(wall.hitbox):
                self.x = old_x
                self.y = old_y

                #  קפיצה לפי סוג הקיר
                if wall.hitbox.width > wall.hitbox.height:
                    # קיר אופקי <- הופכים כיוון אנכי
                    self.rotation = -self.rotation + random.randint(-15 , 15)
                else:
                    # קיר אנכי <- הופכים כיוון אופקי
                    self.rotation = 180 - self.rotation + random.randint(-15 , 15)
                self.bounss -= 1
                break
        for addr,player in players.items():
            if rect.colliderect(player.get_rect()):
                player.hp -= 1
                self.bounss = 0

    def is_finished(self):
        return self.bounss <= 0

    def is_out_of_bounds(self):
        return not (0 <= self.x <= SCREEN_SIZE[0] and 0 <= self.y <= SCREEN_SIZE[1])
