WIDTH = 640
HEIGHT = 680
CELL = 32
COLS = WIDTH // CELL
ROWS = (HEIGHT - 80) // CELL

FPS_DEFAULT = 8

DB_CONFIG = {
    "dbname": "myappdb",
    "user": "postgres",
    "password": "zhangazhanga1409",
    "host": "localhost",
    "port": 5432,
}

BLACK       = (10, 10, 10)
WHITE       = (240, 240, 240)
GRAY        = (90, 90, 90)
LIGHT_GRAY  = (180, 180, 180)
YELLOW      = (240, 200, 60)
BG          = (18, 18, 28)
GRID_COLOR  = (35, 35, 50)
FOOD_NORM   = (80, 200, 120)
FOOD_BONUS  = (240, 200, 60)
FOOD_RARE   = (220, 120, 255)
FOOD_POISON = (150, 30, 30)
PU_SPEED    = (255, 140, 30)
PU_SLOW     = (60, 160, 255)
PU_SHIELD   = (100, 240, 200)
OBSTACLE    = (130, 100, 60)
HUD_BG      = (22, 22, 35)
WALL        = (70, 70, 90)