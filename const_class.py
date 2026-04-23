from pickletools import long4

from const import *
import pygame, math , threading
from enum import Enum

class GameManager:
    def __init__(self):
        self.screen = self.create_screen()
        self.player = None
        self.attacks = []
        self.other_players = []
        self.other_players_attacks = []
        self.background = BackGroundImage(self.screen)
        self.next_attack_id = 0
        self.lock = threading.Lock()
        self.last_info_number = -1

        self.walls = [
            Wall(self.screen, -9, 0, 9, SCREEN_SIZE[1]),
            Wall(self.screen, SCREEN_SIZE[0], 0, 9, SCREEN_SIZE[1]),
            Wall(self.screen, 0, SCREEN_SIZE[1], SCREEN_SIZE[0], 9),
            Wall(self.screen, 0, 0, SCREEN_SIZE[0], 9),
            Wall(self.screen, SCREEN_SIZE[0]/4, SCREEN_SIZE[1]/2, SCREEN_SIZE[0]/2, 9)
        ]
        self.game_state = GameState.WAITING

    def update_screen(self):
        pygame.display.flip()

    def draw_waiting_screen(self):
        with self.lock:
            self.screen.fill((20, 20, 20))
            font = pygame.font.SysFont("arial", 48, bold= True)
            text = font.render("wait...", True, (255, 255, 255))
            rect = text.get_rect(center=(SCREEN_SIZE[0] // 2, SCREEN_SIZE[1] // 2))
            self.screen.blit(text, rect)

    def main_loop(self):
        if self.game_state == GameState.WAITING:
            self.clean_screen()
            self.draw_waiting_screen()
            self.update_screen()

        elif self.game_state == GameState.PLAYING:
            self.clean_screen()
            with self.lock:
                self.background.draw()
            self.draw_walls()
            self.draw_other_players()
            self.update_player()

            self.update_attacks()

            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE]:
                self.Create_attack()
        elif self.game_state == GameState.BEFORE_GAME:
            pass

        self.update_screen()

    def Create_attack(self):
        with self.lock:
            if not self.player:
                return
            now = pygame.time.get_ticks()
            if now - self.player.last_attack_time >= self.player.attack_cooldown:
                attack = Attack(self.player,self.next_attack_id)
                self.next_attack_id += 1
                attack.screen = self.screen
                self.attacks.append(attack)
                self.player.last_attack_time = now
                while(attack.hitBox.colliderect(self.player.hitbox)):
                    attack.action(self.walls)


    def update_attacks(self):
        with self.lock:
            attacks = self.attacks
            for attack in attacks[:]:
                if attack.screen is None:
                    self.del_attack(attack)
                    continue
                attack.action(self.walls)

            for i in attacks[:]:
                for j in attacks[:]:
                    if i != j and i.hitBox.colliderect(j.hitBox):
                        self.del_attack(i)
                        self.del_attack(j)

            for attack in attacks[:]:
                if not self.player:
                    break
                if attack.hitBox.colliderect(self.player.hitbox):
                    self.player.hp -= 1
                    if self.player.hp <= 0:
                        self.player = None
                    self.del_attack(attack)


                for p in self.other_players:
                    if attack.hitBox.colliderect(p.hitbox):
                        self.del_attack(attack)

    def del_attack(self, attack):

        if attack in  self.attacks:
            self.attacks.remove(attack)
        elif attack in self.other_players_attacks:
            self.other_players_attacks.remove(attack)


    def draw_other_players(self):
        with self.lock:
            for i in self.other_players:
                i.draw()

    def draw_walls(self):
        with self.lock:
            for wall in self.walls:
                wall.draw()

    def update_player(self):
        with self.lock:
            if self.player:
                self.player.action_by_key(self.walls, self.other_players)

    def create_screen(self):
        pygame.init()
        screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption(SCREEN_NAME)
        return screen

    def clean_screen(self):
        with self.lock:
            self.screen.fill(SCREEN_COLOR)

    def Add_player(self, player):
        player.screen = self.screen
        self.player = player

    def str(self):
        info = [ i.str() for i in self.attacks ]
        info.append(self.player.str())
        return info

    def update_other_players_and_attacks(self, msg):
        if isinstance(msg, bytes):
            msg = msg.decode()

        if not msg.startswith(INFO.decode() + '|'):
            return

        parts = msg[(len(INFO) + 1):].split('|')
        info_id = int(parts[0])

        if info_id < self.last_info_number:
            return

        self.last_info_number = info_id

        new_attacks_ids = set()

        for part in parts[1:]:
            if part.startswith('PLAYER'):
                fields = part.split(',')
                if len(fields) < 8:
                    continue

                id = int(fields[1])
                x = float(fields[2])
                y = float(fields[3])
                width = float(fields[4])
                height = float(fields[5])
                hp = float(fields[6])
                rotation = float(fields[7])

                found = False
                for p in self.other_players:
                    if p.id == id:
                        p.update(x, y, width, height, rotation, hp)
                        found = True
                        break

                if not found and abs(x+y - self.player.x - self.player.y)> 25:
                    self.other_players.append(
                        Enemy_data(self.screen, x, y, width, height, rotation, hp, id)
                    )

            elif part.startswith('ATTACK'):
                fields = part.split(',')[1:]
                if len(fields) < 7:
                    continue

                x = float(fields[0])
                y = float(fields[1])
                width = float(fields[2])
                height = float(fields[3])
                speed = float(fields[4])
                atk_id = int(fields[5])
                rotation = float(fields[6])

                new_attacks_ids.add(atk_id)

                found = False
                for atk in self.other_players_attacks:
                    if atk.id == atk_id:
                        found = True
                        atk.update(x, y, width, height, speed ,rotation)
                        break

                if not found:
                    self.other_players_attacks.append(
                        Enemy_attack(self.screen, x, y, width, height, speed, atk_id, rotation)
                    )

        self.other_players_attacks = [
            atk for atk in self.other_players_attacks if atk.id in new_attacks_ids
        ]


class Attack:
    def __init__(self, player, id):
        self.screen = None
        self.x, self.y = self.create_pos(player)
        self.id = id
        self.width = player.width * 0.8
        self.height = player.height * 0.8
        self.rotation = player.rotation
        self.speed = player.speed * 2.2

        self.original_image = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.width * 3, self.height * 3))
        self.image = self.original_image

        self.hitBox = pygame.Rect(0, 0, self.width - 9, self.height - 9)
        self.hitBox.center = (self.x, self.y)

        self.bounces = 0
        self.max_bounces = 5


    def create_pos(self, player):
        rad = math.radians(player.rotation)
        dx = math.cos(rad) * 23
        dy = math.sin(rad) * 23
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

    def str(self):
        return (
                GAME.decode() + "|" +
                ATTACK_POS.decode() + "|" +
                ",".join([
                    str(self.x),
                    str(self.y),
                    str(self.width),
                    str(self.height),
                    str(self.speed),
                    str(self.id),
                    str(int(self.rotation))
                ])
        )

class Enemy_attack:
    def __init__(self , screen, x ,y , width , height, speed , id , rotation):
        self.screen = screen
        self.x, self.y = x , y
        self.id = int(id)
        self.width = width
        self.height = height
        self.rotation = rotation
        self.speed = speed

        self.original_image = pygame.image.load(IMAGE_ROOT + "attack.png").convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (self.width * 3, self.height * 3))
        self.image = self.original_image

        self.hitBox = pygame.Rect(0, 0, self.width - 9, self.height - 9)
        self.hitBox.center = (self.x, self.y)

        self.bounces = 0
        self.max_bounces = 5


    def update(self, x ,y, width, height, speed, rotation):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.speed = speed
        self.hitBox.center = (self.x, self.y)
        self.draw()


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


    def draw(self):
        if self.screen:
            rotated = pygame.transform.rotate(self.original_image, -self.rotation)
            self.image = rotated
            image_rect = self.image.get_rect(center=self.hitBox.center)
            self.screen.blit(self.image, image_rect)
            pygame.draw.rect(self.screen, (0, 255, 0), self.hitBox, 1)


class BackGroundImage:
    def __init__(self, screen):
        self.image = pygame.image.load(IMAGE_ROOT + "background.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, SCREEN_SIZE)
        self.screen = screen

    def draw(self):
        self.screen.blit(self.image, (0, 0))


class Tank:
    def __init__(self, screen, x, y, width, height, color, speed, attack_cooldown,hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen
        self.speed = speed
        self.color = color
        self.rotation = 0
        self.hp = hp
        img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()
        self.original_image = pygame.transform.scale(img, (TANK_SIZE * 3, TANK_SIZE * 3))
        self.image = self.original_image

        self.hitbox = pygame.Rect(0, 0, width, height - 3)
        self.hitbox.center = (self.x, self.y)

        self.last_attack_time = 0
        self.attack_cooldown = attack_cooldown

    def action_by_key(self, walls, other_player):
        key = pygame.key.get_pressed()
        if key[pygame.K_w]:
            self.move_by_speed(walls, 1,other_player)
        if key[pygame.K_s]:
            self.move_by_speed(walls, -1, other_player)
        if key[pygame.K_a]:
            self.rotation -= 0.1
        if key[pygame.K_d]:
            self.rotation += 0.1
        self.draw()

    def move_by_speed(self, walls, direction, other_players):
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

        for p in other_players:
            if self.hitbox.colliderect(p.hitbox):
                self.x = old_x
                self.hitbox.center = (self.x, self.y)


        old_y = self.y
        self.y += dy
        self.hitbox.center = (self.x, self.y)

        for wall in walls:
            if self.hitbox.colliderect(wall.hitbox):
                self.y = old_y
                self.hitbox.center = (self.x, self.y)

        for p in other_players:
            if self.hitbox.colliderect(p.hitbox):
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

    def str(self):
        return (
                GAME.decode() + "|" +
                PLAYER_DATA.decode() + "|" +
                ",".join([
                    str(self.x),
                    str(self.y),
                    str(self.width),
                    str(self.height),
                    str(self.hp),
                    str(self.rotation)
                ])
        )


class Wall:
    def __init__(self, screen, x, y, size_x, size_y):
        self.hitbox = pygame.Rect(x, y, size_x, size_y)
        self.screen = screen

    def draw(self):
        pygame.draw.rect(self.screen, (255, 255, 255), self.hitbox)


def main():
    manager = Manager()
    t = Tank(manager.screen, 300, 400, 25, 25, (0, 255, 0), 0.1, 1000)
    manager.Add_player(t)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        manager.main_loop()


class GameState(Enum):
    BEFORE_GAME = 1
    WAITING = 2
    PLAYING = 3


class Enemy_data:
    def __init__(self, screen, x, y, width, height, rotation, hp, id):
        self.screen = screen
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.hp = hp
        self.id = id

        self.hitbox = pygame.Rect(0, 0, width, height - 3)
        self.hitbox.center = (self.x, self.y)

        img = pygame.image.load(IMAGE_ROOT + "tank.png").convert_alpha()
        self.original_image = pygame.transform.scale(img, (width * 3, height * 3))
        self.image = self.original_image

    def draw(self):
        rotated = pygame.transform.rotate(self.original_image, -self.rotation - 90)
        self.image = rotated
        image_rect = self.image.get_rect(center=(self.x, self.y))
        self.screen.blit(self.image, image_rect)
        pygame.draw.rect(self.screen, (0, 255, 0), self.hitbox, 1)
        for i in range(int(self.hp)):
            x = self.x + i * 12 - 20
            y = self.y -22
            pygame.draw.rect(self.screen, (255, 0, 6), (x, y, 5, 5))


    def update(self,x, y, width, height, rotation, hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = rotation
        self.hp = hp
        self.hitbox.center = (self.x, self.y)
