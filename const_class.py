from const import *
import pygame, math


class GameManager:
    def __init__(self):
        self.screen = self.create_screen()
        self.players = {}
        self.attacks = []
        self.background = BackGroundImage(self.screen)

        self.walls = [
            Wall(self.screen, -9, 0, 9, SCREEN_SIZE[1]),
            Wall(self.screen, SCREEN_SIZE[0], 0, 9, SCREEN_SIZE[1]),
            Wall(self.screen, 0, SCREEN_SIZE[1], SCREEN_SIZE[0], 9),
            Wall(self.screen, 0, 0, SCREEN_SIZE[0], 9),
            Wall(self.screen, SCREEN_SIZE[0]/4, SCREEN_SIZE[1]/2, SCREEN_SIZE[0]/2, 9)
        ]

    def update_screen(self):
        pygame.display.flip()

    def main_loop(self,player_id ,cmd = None):
        self.clean_screen()
        self.background.draw()
        self.update_walls()
        if cmd:
            self.update_players(cmd)
        self.update_attacks()
        if cmd:
            if cmd == ATTACK:
                self.Create_attack(self.players[player_id])

        self.update_screen()

    def Create_attack(self, player):
        now = pygame.time.get_ticks()
        if now - player.last_attack_time >= player.attack_cooldown:
            attack = Attack(player)
            attack.screen = self.screen
            self.attacks.append(attack)
            player.last_attack_time = now

    def update_attacks(self):
        for attack in self.attacks[:]:
            if attack.screen is None:
                self.attacks.remove(attack)
                continue
            attack.action(self.walls)

        for attack in self.attacks[:]:
            for id,player in self.players:
                if attack.hitBox.colliderect(player.hitbox):
                    player.hp -= 1
                    if player.hp <= 0:
                        del self.players[id]
                    self.attacks.remove(attack)

    def update_walls(self):
        for wall in self.walls:
            wall.draw()

    def update_players(self,cmd):
        for player in self.players.values():
            player.action_by_key(self.walls,cmd)

    def create_screen(self):
        pygame.init()
        screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption(SCREEN_NAME)
        return screen

    def clean_screen(self):
        self.screen.fill(SCREEN_COLOR)

    def Add_player(self, player,id):
        player.screen = self.screen
        self.players[id] = player


class Attack:
    def __init__(self, player):
        self.screen = None
        self.x, self.y = self.create_pos(player)

        self.width = player.width
        self.height = player.height
        self.rotation = player.rotation
        self.speed = player.speed * 2.2
        self.original_image = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.width * 3, self.height * 3))
        self.image = self.original_image

        self.hitBox = pygame.Rect(0, 0, self.width - 5, self.height - 5)
        self.hitBox.center = (self.x, self.y)

        self.bounces = 0
        self.max_bounces = 3

    def create_pos(self, player):
        rad = math.radians(player.rotation)
        dx = math.cos(rad) * 32
        dy = math.sin(rad) * 32
        return (player.x + dx, player.y + dy)

    def draw(self):
        if self.screen:
            rotated = pygame.transform.rotate(self.original_image, -self.rotation)
            self.image = rotated
            image_rect = self.image.get_rect(center=self.hitBox.center)
            self.screen.blit(self.image, image_rect)
            pygame.draw.rect(self.screen, (0, 255, 0), self.hitBox, 1)

    def action(self, walls):
        old_x, old_y = self.x, self.y

        rad = math.radians(self.rotation)
        dx = math.cos(rad) * self.speed
        dy = math.sin(rad) * self.speed

        self.x += dx
        self.y += dy
        self.hitBox.center = (self.x, self.y)

        for wall in walls:
            if self.hitBox.colliderect(wall.hitbox):

                self.x, self.y = old_x, old_y
                self.hitBox.center = (self.x, self.y)

                if wall.hitbox.width > wall.hitbox.height:
                    self.rotation = -self.rotation
                else:
                    self.rotation = 180 - self.rotation

                self.bounces += 1
                if self.bounces >= self.max_bounces:
                    self.screen = None

                break

        self.draw()


class BackGroundImage:
    def __init__(self, screen):
        self.image = pygame.image.load(IMAGE_ROOT + "background.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, SCREEN_SIZE)
        self.screen = screen

    def draw(self):
        self.screen.blit(self.image, (0, 0))


class Tank:
    def __init__(self, screen, x, y, width, height, color, speed, attack_cooldown):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen
        self.speed = speed
        self.color = color
        self.rotation = 0
        self.hp = 4
        img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()
        self.original_image = pygame.transform.scale(img, (width * 3, height * 3))
        self.image = self.original_image

        self.hitbox = pygame.Rect(0, 0, width, height - 3)
        self.hitbox.center = (self.x, self.y)

        self.last_attack_time = 0
        self.attack_cooldown = attack_cooldown

    def action_by_key(self, walls, cmd):
        if cmd == UP:
            self.move_by_speed(walls, 1)
        if cmd == DOWN:
            self.move_by_speed(walls, -1)
        if cmd == RIGHT:
            self.rotation -= 0.1
        if cmd == LEFT:
            self.rotation += 0.1
        self.draw()

    def move_by_speed(self, walls, direction):
        rad = math.radians(self.rotation)
        dx = math.cos(rad) * self.speed * direction
        dy = math.sin(rad) * self.speed * direction

        old_x = self.x
        self.x += dx
        self.hitbox.center = (self.x, self.y)

        for wall in walls:
            if self.hitbox.colliderect(wall.hitbox):
                self.x = old_x
                self.hitbox.center = (self.x, self.y)

        old_y = self.y
        self.y += dy
        self.hitbox.center = (self.x, self.y)

        for wall in walls:
            if self.hitbox.colliderect(wall.hitbox):
                self.y = old_y
                self.hitbox.center = (self.x, self.y)

    def draw(self):
        rotated = pygame.transform.rotate(self.original_image, -self.rotation - 90)
        self.image = rotated
        image_rect = self.image.get_rect(center=(self.x, self.y))
        self.screen.blit(self.image, image_rect)
        pygame.draw.rect(self.screen, (0, 255, 0), self.hitbox, 1)
        for i in range(self.hp):
            x = self.x + i * 12 - 20
            y = self.y -22
            pygame.draw.rect(self.screen, (255, 0, 6), (x, y, 5, 5))


class Wall:
    def __init__(self, screen, x, y, size_x, size_y):
        self.hitbox = pygame.Rect(x, y, size_x, size_y)
        self.screen = screen

    def draw(self):
        pygame.draw.rect(self.screen, (255, 255, 255), self.hitbox)

