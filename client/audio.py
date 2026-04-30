import pygame
from const import *

class Audio:
    def __init__(self):
        pygame.mixer.init()
        self.background_song = pygame.mixer.Sound(SONG_PATH + BACKGROUND_SONG_PATH)
        self.background_song.set_volume(0.2)

        self.hit_wall = pygame.mixer.Sound(SONG_PATH + HIT_WALL_SONG_PATH)
        self.hit_wall.set_volume(2)

        self.win = pygame.mixer.Sound(SONG_PATH + WIN_SONG_PATH)

        self.lose = pygame.mixer.Sound(SONG_PATH + LOSE_SONG_PATH)
        self.lose.set_volume(1.5)

        self.hit_player = pygame.mixer.Sound(SONG_PATH + HIT_PLAYER_SONG_PATH)

    def play_background_song(self):
        self.background_song.play(loops=-1)


    def play_hit_wall_song(self):
        self.hit_wall.play()

    def play_win_song(self):
        self.win.play()

    def play_lose_song(self):
        self.lose.play()

    def play_hit_player_song(self):
        self.hit_player.play()