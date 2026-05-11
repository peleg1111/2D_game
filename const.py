from enum import Enum

SCREEN_SIZE = (1200, 750)
SCREEN_NAME = "my Game"
SCREEN_COLOR = (50, 50, 50)
FPS = 60
PLAYER_COUNT = 2
WALL_SIZE = 14 * (SCREEN_SIZE[1] / 650) # עובי הקיר
IMAGE_ROOT = 'C:\\Users\\Peleg\\PycharmProjects\\my_game\\images\\'
TIME_BETWEEN_STATES = 6 # זמן המתנה במעבר בין מסכים כמו מסך הפסר למשך הראשי
TIME_BEFORE_REMOVE = 3# [sec]
# רשת
ADDR_SERVER = ("127.0.0.1", 1234)

# הודעות
START_GAME = b"START"
END_CONACTION = b"END_CONACTION"
GAME = b"GAME"
INFO = b"INFO"
WAIT = b"WAIT"
LOSE_GAME = b"LOSE"
WIN_GAME = b"WIN"
WAIT = b"WAIT"
AUDIO = b'AUDIO|'


# מוזיקה
SONG_PATH = "C:\\Users\\Peleg\\PycharmProjects\\my_game\\audio\\"
BACKGROUND_SONG_PATH = 'background_song.mp3'
HIT_WALL_SONG_PATH = 'hit_wall.mp3'
WIN_SONG_PATH = 'win.mp3'
LOSE_SONG_PATH = 'lose.mp3'
HIT_PLAYER_SONG_PATH = 'hit_player.mp3'
CLICK_SONG_PATH = 'click.mp3'

class audio_type(Enum):
    HIT_WALL = '0'
    HIT_PLAYER = '1'