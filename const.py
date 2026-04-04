
SCREEN_SIZE = (800 , 600)
SCREEN_NAME = "my Game"
SCREEN_COLOR = (0,0,0)
FPS = 80
IMAGE_ROOT = 'images\\'


# tank parameters
TANK_SIZE = 25
TANK_HIT_BOX__COLOR = (255,255,255)
TANK_SPEED = 0.1
TANK_ATTACK_COOLDOWN = 1000
TANK_HP = 4


# commands
START_GAME = b"START GAME"
CONNECTION_FAIL = b"Connection Error"
UP = b"UP"
DOWN = b"DOWN"
LEFT = b"LEFT"
RIGHT = b"RIGHT"
ACK = b"ACK"
ACTIONS = [ UP, DOWN, LEFT, RIGHT ]
WAIT = b"WAIT"
GAME = b'GAME'# ה header להודעות של שחקנים שבמהלך המשחק
PLAYER_DATA = b'PLAYER DATA' # GAME|PLAYER_DATA|x,y,width,height,hp
ATTACK_POS = b'ATTACK DATA' # GAME|ATTACK_POS|x,y,width,height,speed,id
INFO = b'INFO' #שרת ללקוח -> העברת כל המיקומים

ADDR_SERVER = ("127.0.0.1", 1234)
