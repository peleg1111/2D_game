import pygame
from const import *

class Song:
    def __init__(self, song_path, volume):
        self.song = pygame.mixer.Sound(SONG_PATH + song_path)
        self.volume = volume
        self.current_volume = volume
        self.set_volume(1)

    def play(self):
        self.song.play()

    def set_volume(self, percent):
        self.current_volume = percent * self.volume
        self.song.set_volume(self.current_volume)

    def infinite_loop(self):
        self.song.play(loops=-1)




class Audio:
    def __init__(self):
        pygame.mixer.init()
        self.background = Song(BACKGROUND_SONG_PATH, 0.2)
        self.hit_wall = Song(HIT_WALL_SONG_PATH, 2)
        self.win = Song(WIN_SONG_PATH, 1)
        self.lose = Song(LOSE_SONG_PATH, 1.5)
        self.hit_player = Song(HIT_PLAYER_SONG_PATH, 1)

    def play_background_song(self):
        self.background.infinite_loop()


    def play_hit_wall_song(self):
        self.hit_wall.play()

    def play_win_song(self):
        self.win.play()

    def play_lose_song(self):
        self.lose.play()

    def play_hit_player_song(self):
        self.hit_player.play()
