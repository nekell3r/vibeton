import pygame

# --- Константы ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE_PLAYER = (60, 120, 220)  # Игрок
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
DARK_GREY = (50, 50, 50)
LIGHT_GREY = (200, 200, 200)

SKY_COLOR_TOP = (100, 150, 255)  # Верхняя часть неба
SKY_COLOR_BOTTOM = (170, 210, 255)  # Нижняя часть неба
BUILDING_COLORS = [(100, 100, 120), (120, 120, 140), (80, 80, 100), (140, 140, 160)]
WINDOW_COLOR = (200, 200, 255, 100)  # Полупрозрачные окна
ROAD_COLOR = (70, 70, 70)
ROAD_LINE_COLOR = (220, 220, 0)
UI_TEXT_COLOR = (230, 230, 230)
UI_BG_COLOR = (30, 30, 30, 180)  # Полупрозрачный фон для UI
TOAST_TEXT_COLOR = WHITE
TOAST_BG_COLOR = (0, 0, 0, 200)

# Параметры игры
LANE_YS = [SCREEN_HEIGHT * 0.58, SCREEN_HEIGHT * 0.73, SCREEN_HEIGHT * 0.88]
PLAYER_START_X = 150
INITIAL_SPEED = 4.5
SPEED_INCREMENT = 0.2
SPEED_INCREMENT_INTERVAL_SEC = 10
GAME_DURATION_SEC = 90
INITIAL_HEALTH = 3

PLAYER_SIZE = (35, 55)
OBSTACLE_BASE_SIZE = 50
BOOSTER_RADIUS = 20

# Типы полисов и рисков
POLICY_COLORS = {"kasko": GREEN, "dms": CYAN, "property": YELLOW, "travel": MAGENTA}
RISK_COLORS = {"tree": (100, 60, 20), "phone": (100, 100, 110), "accident": RED, "bill": ORANGE}

POLICY_TYPES = list(POLICY_COLORS.keys())
RISK_TYPES = list(RISK_COLORS.keys())
RISK_PROTECTION = {"tree": "property", "phone": "property", "accident": "kasko", "bill": "dms"}
RISK_COSTS = {"tree": 30000, "phone": 15000, "accident": 50000, "bill": 25000}
TIPS_DATA = {
    "tree": f"Имущество от дерева! Экономия: {RISK_COSTS['tree']:,}₽",
    "phone": f"Имущество за телефон! Экономия: {RISK_COSTS['phone']:,}₽",
    "accident": f"КАСКО от аварии! Экономия: {RISK_COSTS['accident']:,}₽",
    "bill": f"ДМС за счет! Экономия: {RISK_COSTS['bill']:,}₽"
} 