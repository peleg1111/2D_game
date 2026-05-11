import random
from enum import Enum

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
    def __init__(self, x, y, rotation, speed = 3.5):
        rad = math.radians(rotation)
        self.x = x + math.cos(rad) * (23 * SCREEN_SIZE[1] / 600 )
        self.y = y + math.sin(rad) * (23 * SCREEN_SIZE[1] / 600 )
        self.rotation = rotation
        self.speed = speed
        self.bounss = 10

    def update(self, walls, players):
        ttl = self.bounss

        old_x = self.x
        old_y = self.y

        rad = math.radians(self.rotation)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        rect = self.get_rect()

        for wall in walls:
            if rect.colliderect(wall.hitbox):
                self.x = old_x
                self.y = old_y
                dx = math.cos(rad)
                dy = math.sin(rad)

                if abs(rect.right - wall.hitbox.left) < 5:
                    normal = (-1, 0)  # פגיעה מצד ימין של הקיר

                elif abs(rect.left - wall.hitbox.right) < 5:
                    normal = (1, 0)  # פגיעה מצד שמאל

                elif abs(rect.bottom - wall.hitbox.top) < 5:
                    normal = (0, -1)  # פגיעה מלמטה

                elif abs(rect.top - wall.hitbox.bottom) < 5:
                    normal = (0, 1)  # פגיעה מלמעלה

                else:
                    normal = (dx * -1, dy * -1)# פגיעה בפינה <-- נורמל אלכסוני

                dot = dx * normal[0] + dy * normal[1]
                rx = dx - 2 * dot * normal[0]
                ry = dy - 2 * dot * normal[1]
                self.rotation = math.degrees(math.atan2(ry, rx)) + random.randint(-5 , 6)
                self.bounss -= 1
                break

        for addr,player in players.items():
            if rect.colliderect(player.get_rect()):
                player.hp -= 1
                self.bounss = 0
                return audio_type.HIT_PLAYER
        if self.bounss != ttl:
            return audio_type.HIT_WALL
        return None

    def is_finished(self):
        return self.bounss <= 0

    def is_out_of_bounds(self):
        return not (0 <= self.x <= SCREEN_SIZE[0] and 0 <= self.y <= SCREEN_SIZE[1])

    def get_rect(self):
        return pygame.Rect(self.x - 3, self.y - 3, 8 * (SCREEN_SIZE[1]/650), 8 * (SCREEN_SIZE[1]/650))

class Wall:
    def __init__(self, x, y, w, h):
        self.hitbox = pygame.Rect(x, y, w, h)