import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (50, 200, 50)
DARK_RED = (80, 0, 0)
BG_COLOR = (30, 30, 30)

SAVE_FILE = "savegame.json"

ASSETS_DIR = resource_path('assets')
