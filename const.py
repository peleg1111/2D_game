__author__ = 'Peleg Etzioni'
from enum import Enum

# קבועים
SCREEN_SIZE = (1200, 750)
SCREEN_NAME = "my Game"
SCREEN_COLOR = (50, 50, 50)
FPS = 80
PLAYER_COUNT = 2
WALL_SIZE = 14 * (SCREEN_SIZE[1] / 650) # עובי הקיר
IMAGE_ROOT = 'images\\'
TIME_BETWEEN_STATES = 6 # זמן המתנה במעבר בין מסכים כמו מסך הפסד למשך הראשי
TIME_BEFORE_REMOVE = 3# [sec]
ENCRIPTION_PATH = 'encryption_key\\'

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
WALLS = b'WALLS'

DEBUG = True
ENC_HELLO = b"ENC_HELLO"
ENC_PARAMS = b"ENC_PARAMS"
ENC_PUBKEY = b"ENC_PUBKEY"
ENC_DONE = b"ENC_DONE"
NOT_ENCRYPTED = b"NOT_ENCRYPTED"

# מוזיקה
SONG_PATH = "audio\\"
BACKGROUND_SONG_PATH = 'background_song.mp3'
HIT_WALL_SONG_PATH = 'hit_wall.mp3'
WIN_SONG_PATH = 'win.mp3'
LOSE_SONG_PATH = 'lose.mp3'
HIT_PLAYER_SONG_PATH = 'hit_player.mp3'
CLICK_SONG_PATH = 'click.mp3'


# יצירת המבוך
W, H = SCREEN_SIZE
S = WALL_SIZE

MAZE_1 = [
    (0, 0, W, S),
    (0, H-S, W, S),
    (0, 0, S, H),
    (W-S,  0, S, H),
    (W*0.29, S, S, H*0.26),
    (W*0.70, S, S, H*0.26),
    (S, H*0.40, W*0.20, S),
    (W*0.22, H*0.21, S, H*0.20),
    (W*0.77, H*0.40, W*0.22, S),
    (W*0.77, H*0.21, S, H*0.20),
    (W*0.49, S, S, H*0.19),
    (S, H*0.61, W*0.24, S),
    (W*0.21, H*0.61, S, H*0.16),
    (W*0.79, H*0.77, W*0.20, S),
    (W*0.79, H*0.61, S, H*0.16),
    (W*0.35, H*0.73, S, H*0.26),
    (W*0.64, H*0.73, S, H*0.26),
    (W*0.44, H*0.25, W*0.12, S),
    (W*0.49, H*0.25, S, H*0.12),
    (W*0.44, H*0.70, W*0.12, S),
    (W*0.49, H*0.61, S, H*0.10),
]

MAZE_2 = [
    (0, 0, W, S),
    (0, H-S, W, S),
    (0, 0, S, H),
    (W-S, 0, S, H),
    (W*0.1, H*0.45, W*0.8, S),
    (W*0.48, H*0.1, S, H*0.8),
    (W*0.1, H*0.1, W*0.25, S),
    (W*0.1, H*0.1, S, H*0.25),
    (W*0.65, H*0.1, W*0.25, S),
    (W*0.9-S, H*0.1, S, H*0.25),
    (W*0.25, H*0.25, W*0.15, S),
    (W*0.6,  H*0.25, W*0.15, S),
    (W*0.1, H*0.65, W*0.25, S),
    (W*0.1, H*0.65, S, H*0.25),
    (W*0.65, H*0.65, W*0.25, S),
    (W*0.9-S, H*0.65, S, H*0.25),
    (W*0.25, H*0.55, W*0.15, S),
    (W*0.6,  H*0.55, W*0.15, S),
    (W*0.45, H*0.45, W*0.1, S),
]

MAZE_3 = [
    (0, 0, W, S),
    (0, H - S, W, S),
    (0, 0, S, H),
    (W - S, 0, S, H),
    (W * 0.15, H * 0.10, W * 0.18, S),
    (W * 0.55, H * 0.10, W * 0.18, S),
    (W * 0.10, H * 0.22, S, H * 0.18),
    (W * 0.38, H * 0.15, S, H * 0.18),
    (W * 0.62, H * 0.15, S, H * 0.18),
    (W * 0.88, H * 0.22, S, H * 0.18),
    (W * 0.22, H * 0.35, W * 0.18, S),
    (W * 0.60, H * 0.35, W * 0.18, S),
    (W * 0.10, H * 0.44, S, H * 0.18),
    (W * 0.48, H * 0.38, S, H * 0.18),
    (W * 0.88, H * 0.44, S, H * 0.18),
    (W * 0.22, H * 0.5, W * 0.18, S),
    (W * 0.60, H * 0.5, W * 0.18, S),
    (W * 0.10, H * 0.66, S, H * 0.18),
    (W * 0.35, H * 0.62, S, H * 0.18),
    (W * 0.65, H * 0.62, S, H * 0.18),
    (W * 0.88, H * 0.66, S, H * 0.18),
    (W * 0.28, H * 0.85, S, H * 0.12),
    (W * 0.48, H * 0.82, W * 0.18, S),
    (W * 0.72, H * 0.85, S, H * 0.12),
]

ALL_MAZES = {
    1: MAZE_1,
    2: MAZE_2,
    3: MAZE_3,
}