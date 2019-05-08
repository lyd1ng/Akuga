from Akuga.ArenaCreator import CreateArena


DEBUG = True
BOARD_WIDTH = 6
BOARD_HEIGHT = 6
SCREEN_DIMENSION = (640, 480)
MAX_PLAYERS = 2
# Has to be set before the game starts
CURRENT_PLAYER = None
PLAYERS = []
ARENA = CreateArena(BOARD_WIDTH, BOARD_HEIGHT, 0, 250)
