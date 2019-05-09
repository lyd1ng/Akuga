from Akuga.ArenaCreator import CreateArena


DEBUG = True
BOARD_WIDTH = 2
BOARD_HEIGHT = 2
SCREEN_DIMENSION = (640, 480)
ARENA = CreateArena(BOARD_WIDTH, BOARD_HEIGHT, 0, 250)
# Will be set within the main before the game starts
PLAYER_CHAIN = None
