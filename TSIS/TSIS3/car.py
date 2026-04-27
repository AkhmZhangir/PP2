import pygame
import random
import json
import os
import sys
from datetime import datetime

# Инициализация Pygame и модуля шрифтов
pygame.init()
pygame.font.init()

# ─── Константы экрана ────────────────────────────────────────────────────────
WIDTH, HEIGHT = 480, 720                                  # Размер окна игры (ширина x высота)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))         # Создание окна с заданными размерами
pygame.display.set_caption("TSIS 3 Racer Game")           # Заголовок окна
CLOCK = pygame.time.Clock()                               # Объект для управления FPS
FPS = 60                                                  # Целевой FPS

# ─── Цветовая палитра ─────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (20,  20,  20)
GRAY       = (120, 120, 120)
LIGHT_GRAY = (200, 200, 200)
RED        = (220, 60,  60)
GREEN      = (60,  200, 100)
BLUE       = (70,  140, 255)
YELLOW     = (240, 210, 70)
ORANGE     = (255, 150, 50)
PURPLE     = (170, 90,  220)
CYAN       = (70,  220, 220)
BG         = (35,  35,  35)    # Цвет фона за пределами дороги
ROAD       = (70,  70,  70)    # Цвет асфальта
ROAD_LINE  = (240, 240, 240)   # Цвет разметки полос
BARRIER    = (190, 80,  80)    # Цвет барьера-препятствия
OIL        = (30,  30,  30)    # Цвет масляного пятна
POTHOLE    = (100, 70,  50)    # Цвет выбоины
SLOW       = (80,  140, 255)   # Цвет зоны замедления

# ─── Шрифты ───────────────────────────────────────────────────────────────────
FONT_BIG   = pygame.font.SysFont("arial", 42, bold=True)  # Крупный заголовок
FONT_MED   = pygame.font.SysFont("arial", 28, bold=True)  # Средний текст
FONT_SMALL = pygame.font.SysFont("arial", 20)             # Основной интерфейс
FONT_TINY  = pygame.font.SysFont("arial", 16)             # Мелкий вспомогательный текст

# ─── Пути к файлам сохранений ────────────────────────────────────────────────
SETTINGS_FILE    = "settings.json"     # Файл настроек игры
LEADERBOARD_FILE = "leaderboard.json"  # Файл таблицы рекордов

# Настройки по умолчанию, используются при первом запуске или сбросе
DEFAULT_SETTINGS = {
    "sound":      True,
    "car_color":  "red",
    "difficulty": "normal"
}

# Множители сложности: speed — скорость дороги, traffic — частота машин, obstacle — частота препятствий
DIFFICULTY_PRESETS = {
    "easy":   {"speed_mul": 0.9,  "traffic_mul": 0.8,  "obstacle_mul": 0.8},
    "normal": {"speed_mul": 1.0,  "traffic_mul": 1.0,  "obstacle_mul": 1.0},
    "hard":   {"speed_mul": 1.15, "traffic_mul": 1.2,  "obstacle_mul": 1.25},
}

# Соответствие ключей цветов их RGB-значениям для машины игрока
CAR_COLORS = {
    "red":    RED,
    "blue":   BLUE,
    "green":  GREEN,
    "yellow": YELLOW
}

# ─── Состояния игры (конечный автомат) ───────────────────────────────────────
STATE_MAIN_MENU   = "MAIN_MENU"
STATE_USERNAME    = "USERNAME"
STATE_SETTINGS    = "SETTINGS"
STATE_LEADERBOARD = "LEADERBOARD"
STATE_PLAYING     = "PLAYING"
STATE_GAME_OVER   = "GAME_OVER"

# ─── Параметры полос движения ─────────────────────────────────────────────────
LANE_COUNT  = 5                                    # Количество полос
ROAD_MARGIN = 70                                   # Отступ дороги от края экрана
ROAD_WIDTH  = WIDTH - ROAD_MARGIN * 2              # Ширина проезжей части
LANE_WIDTH  = ROAD_WIDTH // LANE_COUNT             # Ширина одной полосы
# Центры полос по оси X — используются для позиционирования объектов
LANE_X = [ROAD_MARGIN + i * LANE_WIDTH + LANE_WIDTH // 2 for i in range(LANE_COUNT)]

# ─── Игровые константы ───────────────────────────────────────────────────────
FINISH_DISTANCE    = 10000   # Дистанция до финиша в условных единицах
SAFE_SPAWN_DISTANCE = 260    # Минимальное расстояние спауна от игрока по Y
MIN_VERTICAL_GAP   = 130     # Минимальный вертикальный зазор между объектами на одной полосе


# ─── Утилиты: работа с JSON ───────────────────────────────────────────────────

def load_json(path, default_data):
    """Загружает JSON-файл по указанному пути.
    Если файл не найден или повреждён — создаёт его с данными по умолчанию."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        # При ошибке чтения — перезаписываем файл значениями по умолчанию
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data


def save_json(path, data):
    """Сохраняет данные в JSON-файл с отступами для читаемости."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_settings():
    """Загружает настройки игры из settings.json."""
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())


def save_settings(settings):
    """Сохраняет текущие настройки в settings.json."""
    save_json(SETTINGS_FILE, settings)


def load_leaderboard():
    """Загружает таблицу рекордов из leaderboard.json."""
    return load_json(LEADERBOARD_FILE, [])


def save_leaderboard(entries):
    """Сохраняет список рекордов в leaderboard.json."""
    save_json(LEADERBOARD_FILE, entries)


def add_score_to_leaderboard(name, score, distance, coins):
    """Добавляет новую запись в таблицу рекордов.
    Сортирует по убыванию очков и дистанции, сохраняет только топ-10."""
    data = load_leaderboard()
    data.append({
        "name":     name,
        "score":    int(score),
        "distance": int(distance),
        "coins":    int(coins),
        "date":     datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    # Первичная сортировка по очкам, вторичная — по дистанции
    data.sort(key=lambda x: (x["score"], x["distance"]), reverse=True)
    data = data[:10]  # Оставляем только 10 лучших результатов
    save_leaderboard(data)


def draw_text(text, font, color, surface, x, y, center=False):
    """Рендерит текст на указанную поверхность.
    При center=True текст центрируется вокруг точки (x, y)."""
    img  = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center   = (x, y)
    else:
        rect.topleft  = (x, y)
    surface.blit(img, rect)


# ─── Класс кнопки ─────────────────────────────────────────────────────────────

class Button:
    """Интерактивная кнопка с подсветкой при наведении курсора."""

    def __init__(self, x, y, w, h, text, bg=GRAY, hover=LIGHT_GRAY, fg=WHITE):
        self.rect  = pygame.Rect(x, y, w, h)  # Прямоугольная область кнопки
        self.text  = text    # Надпись на кнопке
        self.bg    = bg      # Основной цвет фона
        self.hover = hover   # Цвет при наведении
        self.fg    = fg      # Цвет текста

    def draw(self, surface):
        """Рисует кнопку; меняет цвет при наведении мыши."""
        mouse = pygame.mouse.get_pos()
        color = self.hover if self.rect.collidepoint(mouse) else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE,  self.rect, 2, border_radius=12)  # Рамка
        draw_text(self.text, FONT_SMALL, self.fg, surface,
                  self.rect.centerx, self.rect.centery, center=True)

    def clicked(self, event):
        """Возвращает True, если по кнопке было выполнено нажатие ЛКМ."""
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ─── Класс машины игрока ──────────────────────────────────────────────────────

class PlayerCar:
    """Управляемый автомобиль игрока.
    Перемещается по полосам; поддерживает кулдаун движения и таймер дрейфа."""

    def __init__(self, color_name):
        self.width  = 48
        self.height = 88
        self.lane   = 1                              # Начальная полоса (индекс)
        self.x      = LANE_X[self.lane] - self.width  // 2
        self.y      = HEIGHT - 130                  # Фиксированная позиция по Y в нижней части экрана
        self.color_name   = color_name
        self.color        = CAR_COLORS[color_name]
        self.rect         = pygame.Rect(self.x, self.y, self.width, self.height)
        self.move_cooldown = 0    # Задержка между сменами полосы (в кадрах)
        self.drift_timer   = 0   # Таймер эффекта дрейфа (от масляного пятна)

    def set_color(self, color_name):
        """Обновляет цвет машины при изменении настроек."""
        self.color_name = color_name
        self.color      = CAR_COLORS[color_name]

    def move_left(self):
        """Сдвигает машину на одну полосу влево, если это возможно."""
        if self.lane > 0:
            self.lane -= 1
            self.x = LANE_X[self.lane] - self.width // 2

    def move_right(self):
        """Сдвигает машину на одну полосу вправо, если это возможно."""
        if self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.x = LANE_X[self.lane] - self.width // 2

    def update(self):
        """Обновляет прямоугольник коллизий и уменьшает таймеры."""
        self.rect.topleft = (self.x, self.y)
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
        if self.drift_timer > 0:
            self.drift_timer -= 1

    def draw(self, surface):
        """Рисует машину: кузов, лобовое стекло и четыре колеса."""
        body = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, body, border_radius=10)          # Кузов
        pygame.draw.rect(surface, WHITE,      body, 2,   border_radius=10)     # Контур кузова
        # Лобовое стекло
        pygame.draw.rect(surface, CYAN,
                         (self.x + 8, self.y + 10, self.width - 16, 18), border_radius=6)
        # Колёса (чёрные круги по углам)
        pygame.draw.circle(surface, BLACK, (self.x + 10,              self.y + 16),              6)
        pygame.draw.circle(surface, BLACK, (self.x + self.width - 10, self.y + 16),              6)
        pygame.draw.circle(surface, BLACK, (self.x + 10,              self.y + self.height - 14), 6)
        pygame.draw.circle(surface, BLACK, (self.x + self.width - 10, self.y + self.height - 14), 6)


# ─── Класс транспортного автомобиля ──────────────────────────────────────────

class TrafficCar:
    """Встречный автомобиль-противник.
    Движется сверху вниз с заданной скоростью; при столкновении — авария."""

    def __init__(self, lane, speed):
        self.width  = 46
        self.height = 84
        self.lane   = lane
        self.x      = LANE_X[lane] - self.width // 2
        # Спаун за верхним краем экрана со случайным смещением
        self.y      = -self.height - random.randint(20, 120)
        self.speed  = speed                                       # Собственная скорость машины
        self.color  = random.choice([BLUE, GREEN, YELLOW, ORANGE, PURPLE])  # Случайный цвет
        self.rect   = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        """Смещает машину вниз с учётом скорости дороги и собственной скорости."""
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        """Рисует транспортный автомобиль с лобовым стеклом."""
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE,      self.rect, 2, border_radius=10)
        pygame.draw.rect(surface, CYAN,
                         (self.x + 8, self.y + 10, self.width - 16, 16), border_radius=5)


# ─── Класс препятствия ────────────────────────────────────────────────────────

class Obstacle:
    """Статическое препятствие на дороге.
    Типы: barrier (авария), oil (дрейф), pothole (замедление), slow_zone (сильное замедление)."""

    def __init__(self, lane, kind, speed):
        self.lane  = lane
        self.kind  = kind
        self.speed = speed
        # Барьеры и зоны замедления — шире; масляные пятна и выбоины — ниже
        self.width  = 52 if kind in ("barrier", "slow_zone") else 42
        self.height = 28 if kind in ("oil", "pothole")       else 36
        self.x    = LANE_X[lane] - self.width  // 2
        self.y    = -self.height - random.randint(20, 120)   # Спаун за экраном
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        """Движет препятствие вниз вместе с дорогой."""
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        """Рисует препятствие в зависимости от его типа."""
        if self.kind == "barrier":
            # Красный прямоугольный барьер
            pygame.draw.rect(surface, BARRIER, self.rect, border_radius=6)
            pygame.draw.rect(surface, WHITE,   self.rect, 2, border_radius=6)
        elif self.kind == "oil":
            # Тёмный эллипс масляного пятна
            pygame.draw.ellipse(surface, OIL,        self.rect)
            pygame.draw.ellipse(surface, LIGHT_GRAY, self.rect, 2)
        elif self.kind == "pothole":
            # Коричневая выбоина в дороге
            pygame.draw.ellipse(surface, POTHOLE, self.rect)
            pygame.draw.ellipse(surface, BLACK,   self.rect, 2)
        elif self.kind == "slow_zone":
            # Синяя зона принудительного замедления
            pygame.draw.rect(surface, SLOW,  self.rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=6)


# ─── Класс бонуса (Power-Up) ──────────────────────────────────────────────────

class PowerUp:
    """Подбираемый бонус на дороге.
    Типы: nitro (ускорение), shield (щит), repair (починка).
    Исчезает через 7 секунд, если не подобран."""

    def __init__(self, lane, ptype, speed):
        self.lane  = lane
        self.type  = ptype
        self.speed = speed
        self.size  = 28
        self.x     = LANE_X[lane] - self.size // 2
        self.y     = -self.size - random.randint(20, 120)
        self.rect  = pygame.Rect(self.x, self.y, self.size, self.size)
        self.life_ms    = 7000                       # Время жизни бонуса в миллисекундах
        self.spawn_time = pygame.time.get_ticks()    # Момент появления

    def update(self, road_speed):
        """Смещает бонус вниз вместе с дорогой."""
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def expired(self):
        """Возвращает True, если бонус не подобран дольше 7 секунд."""
        return pygame.time.get_ticks() - self.spawn_time > self.life_ms

    def draw(self, surface):
        """Рисует бонус как цветной круг с буквенным обозначением типа."""
        color = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}[self.type]
        pygame.draw.circle(surface, color, self.rect.center, self.size // 2)
        pygame.draw.circle(surface, WHITE, self.rect.center, self.size // 2, 2)
        # Буква-идентификатор: N — Nitro, S — Shield, R — Repair
        label = {"nitro": "N", "shield": "S", "repair": "R"}[self.type]
        draw_text(label, FONT_SMALL, BLACK, surface,
                  self.rect.centerx, self.rect.centery, center=True)


# ─── Класс дорожного события ──────────────────────────────────────────────────

class RoadEvent:
    """Динамическое событие на трассе.
    Типы:
        moving_barrier — движущийся барьер, отскакивающий от краёв дороги;
        speed_bump     — лежачий полицейский, кратковременно замедляет;
        nitro_strip    — полоса ускорения, даёт временный нитро-буст."""

    def __init__(self, etype, lane, speed):
        self.type     = etype
        self.lane     = lane
        self.speed    = speed
        self.finished = False

        if etype == "moving_barrier":
            self.width     = 50
            self.height    = 26
            self.x         = LANE_X[lane] - self.width // 2
            self.y         = -60
            self.direction = random.choice([-1, 1])   # Начальное направление горизонтального движения
            self.rect      = pygame.Rect(self.x, self.y, self.width, self.height)

        elif etype == "speed_bump":
            self.width  = LANE_WIDTH - 14
            self.height = 16
            self.x      = LANE_X[lane] - self.width // 2
            self.y      = -40
            self.rect   = pygame.Rect(self.x, self.y, self.width, self.height)

        else:  # nitro_strip
            self.width  = LANE_WIDTH - 18
            self.height = 70
            self.x      = LANE_X[lane] - self.width // 2
            self.y      = -100
            self.rect   = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        """Обновляет позицию события.
        Движущийся барьер дополнительно перемещается горизонтально и отражается от краёв."""
        self.y += self.speed + road_speed
        if self.type == "moving_barrier":
            self.x += self.direction * 2.2
            left_limit  = ROAD_MARGIN
            right_limit = ROAD_MARGIN + ROAD_WIDTH - self.width
            if self.x <= left_limit or self.x >= right_limit:
                self.direction *= -1   # Отражение от границ дороги
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        """Рисует событие в соответствии с его типом."""
        if self.type == "moving_barrier":
            # Фиолетовый движущийся барьер
            pygame.draw.rect(surface, PURPLE, self.rect, border_radius=5)
            pygame.draw.rect(surface, WHITE,  self.rect, 2, border_radius=5)
        elif self.type == "speed_bump":
            # Жёлтый лежачий полицейский
            pygame.draw.rect(surface, YELLOW, self.rect, border_radius=4)
            pygame.draw.rect(surface, BLACK,  self.rect, 2, border_radius=4)
        elif self.type == "nitro_strip":
            # Оранжевая нитро-полоса с горизонтальными линиями
            pygame.draw.rect(surface, ORANGE, self.rect, border_radius=4)
            for i in range(4):
                pygame.draw.line(surface, WHITE,
                                 (self.x + 6,              self.y + 10 + i * 14),
                                 (self.x + self.width - 6, self.y + 10 + i * 14), 2)


# ─── Главный класс игры ───────────────────────────────────────────────────────

class Game:
    """Центральный объект игры.
    Управляет состояниями (конечный автомат), объектами сцены, HUD,
    спауном противников, обработкой событий, обновлением физики и отрисовкой."""

    def __init__(self):
        self.settings          = load_settings()       # Загружаем сохранённые настройки
        self.running           = True                  # Флаг главного цикла
        self.state             = STATE_MAIN_MENU       # Начальное состояние — главное меню
        self.username          = ""                    # Имя текущего игрока
        self.road_offset       = 0                     # Смещение разметки дороги для анимации
        self.leaderboard_saved = False                 # Флаг: результат уже сохранён в таблицу

        # ── Кнопки главного меню ──────────────────────────────────────────────
        self.menu_buttons = [
            Button(WIDTH // 2 - 100, 260, 200, 55, "Play"),
            Button(WIDTH // 2 - 100, 330, 200, 55, "Leaderboard"),
            Button(WIDTH // 2 - 100, 400, 200, 55, "Settings"),
            Button(WIDTH // 2 - 100, 470, 200, 55, "Quit"),
        ]

        # ── Переиспользуемые кнопки навигации ────────────────────────────────
        self.back_button      = Button(20, 20, 110, 45, "Back")
        self.retry_button     = Button(WIDTH // 2 - 100, 470, 200, 55, "Retry")
        self.main_menu_button = Button(WIDTH // 2 - 100, 540, 200, 55, "Main Menu")

        # ── Кнопки экрана настроек (текст обновляется динамически) ───────────
        self.sound_button         = Button(WIDTH // 2 - 100, 220, 200, 50, "")
        self.color_button         = Button(WIDTH // 2 - 100, 300, 200, 50, "")
        self.diff_button          = Button(WIDTH // 2 - 100, 380, 200, 50, "")
        self.settings_back_button = Button(WIDTH // 2 - 100, 470, 200, 55, "Back")

        self.start_run()   # Инициализируем первый забег

    def start_run(self):
        """Сбрасывает все игровые переменные и подготавливает новый забег."""
        self.player         = PlayerCar(self.settings["car_color"])
        self.score          = 0
        self.coins          = 0
        self.distance       = 0
        # Базовая скорость дороги масштабируется по сложности
        self.base_speed     = 5.0 * DIFFICULTY_PRESETS[self.settings["difficulty"]]["speed_mul"]
        self.road_speed     = self.base_speed
        self.game_over      = False

        # ── Состояние бонусов ─────────────────────────────────────────────────
        self.shield_active   = False   # Активен ли щит
        self.repair_count    = 0       # Количество зарядов починки
        self.active_powerup  = None    # Текущий активный бонус
        self.powerup_end_time = 0      # Время окончания нитро (мс)
        self.slow_timer      = 0       # Оставшееся время замедления (кадры)

        # ── Списки игровых объектов ───────────────────────────────────────────
        self.traffic     = []
        self.obstacles   = []
        self.powerups    = []
        self.road_events = []
        self.coin_items  = []

        # ── Таймеры спауна (в кадрах) ─────────────────────────────────────────
        self.spawn_traffic_timer  = 0
        self.spawn_obstacle_timer = 0
        self.spawn_powerup_timer  = 0
        self.spawn_event_timer    = 0

        self.leaderboard_saved = False

    def get_level(self):
        """Возвращает текущий уровень сложности.
        Уровень растёт каждые 500 единиц пройденной дистанции."""
        return 1 + int(self.distance // 500)

    def get_player_rect(self):
        """Возвращает прямоугольник коллизий машины игрока."""
        return self.player.rect

    def can_spawn_lane(self, lane, new_y, objects):
        """Проверяет, безопасно ли спаунить объект в указанной полосе.
        Запрещает спаун на полосе игрока вблизи него и слишком близко к другим объектам."""
        if lane == self.player.lane and new_y > -SAFE_SPAWN_DISTANCE:
            return False
        for obj in objects:
            if hasattr(obj, "lane") and obj.lane == lane and abs(obj.y - new_y) < MIN_VERTICAL_GAP:
                return False
        return True

    def choose_safe_lane(self, existing_objects):
        """Случайно выбирает безопасную полосу для спауна нового объекта.
        Возвращает None, если безопасных полос не осталось."""
        lanes = list(range(LANE_COUNT))
        random.shuffle(lanes)
        for lane in lanes:
            if self.can_spawn_lane(lane, -80, existing_objects):
                return lane
        return None

    def spawn_traffic(self):
        """Создаёт новый транспортный автомобиль на случайной безопасной полосе.
        Скорость увеличивается с уровнем."""
        lane = self.choose_safe_lane(self.traffic + self.obstacles)
        if lane is not None:
            speed = random.uniform(1.0, 2.8) + self.get_level() * 0.15
            self.traffic.append(TrafficCar(lane, speed))

    def spawn_obstacle(self):
        """Создаёт случайное препятствие (барьер, масло, выбоина, зона замедления)
        на безопасной полосе с весовым распределением типов."""
        lane = self.choose_safe_lane(self.traffic + self.obstacles)
        if lane is not None:
            kind = random.choices(
                ["barrier", "oil", "pothole", "slow_zone"],
                weights=[30, 25, 25, 20],
                k=1
            )[0]
            speed = random.uniform(0.7, 1.8)
            self.obstacles.append(Obstacle(lane, kind, speed))

    def spawn_powerup(self):
        """Создаёт случайный бонус на безопасной полосе."""
        lane = self.choose_safe_lane(self.traffic + self.obstacles + self.powerups)
        if lane is not None:
            ptype = random.choice(["nitro", "shield", "repair"])
            self.powerups.append(PowerUp(lane, ptype, 1.2))

    def spawn_event(self):
        """Создаёт случайное дорожное событие на произвольной полосе."""
        etype = random.choice(["moving_barrier", "speed_bump", "nitro_strip"])
        lane  = random.randint(0, LANE_COUNT - 1)
        self.road_events.append(RoadEvent(etype, lane, 1.2))

    def apply_powerup(self, ptype):
        """Применяет подобранный бонус.
        Repair накапливается (макс. 1), остальные бонусы не стекаются."""
        if ptype == "repair":
            self.repair_count = min(1, self.repair_count + 1)
            self.score += 40
            return

        # Запрещаем активацию второго бонуса при уже активном
        if self.active_powerup is not None:
            return

        self.active_powerup = ptype
        if ptype == "nitro":
            # Случайная длительность нитро от 3 до 5 секунд
            self.powerup_end_time = pygame.time.get_ticks() + random.randint(3000, 5000)
        elif ptype == "shield":
            self.shield_active    = True
            self.powerup_end_time = 0

    def clear_active_powerup(self):
        """Деактивирует текущий бонус и восстанавливает базовую скорость."""
        if self.active_powerup == "nitro":
            self.road_speed = max(self.base_speed, self.road_speed)
        self.active_powerup = None

    def handle_crash(self, remove_obj=None):
        """Обрабатывает столкновение.
        Щит поглощает удар → исчезает. Repair восстанавливает ход.
        Если защиты нет — устанавливает флаг game_over и переходит в STATE_GAME_OVER."""
        if self.shield_active:
            self.shield_active  = False
            self.active_powerup = None
            self.score += 100
            return False
        if self.repair_count > 0:
            self.repair_count -= 1
            self.score += 50
            return False
        self.game_over = True
        self.state     = STATE_GAME_OVER
        return True

    def update_playing(self):
        """Основной игровой тик: обновляет физику, таймеры, спаун,
        коллизии, очки и проверяет условия конца забега."""
        if self.game_over:
            return

        level = self.get_level()
        diff  = DIFFICULTY_PRESETS[self.settings["difficulty"]]

        # Базовая скорость плавно растёт с уровнем и масштабируется по сложности
        self.base_speed = (5.0 + level * 0.18) * diff["speed_mul"]
        self.road_speed = self.base_speed

        # Замедление от масла/выбоин/лежачих полицейских
        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.road_speed *= 0.65

        # Нитро-ускорение увеличивает скорость на 75%; по истечении — сброс
        if self.active_powerup == "nitro":
            if pygame.time.get_ticks() < self.powerup_end_time:
                self.road_speed *= 1.75
            else:
                self.clear_active_powerup()

        # Анимация разметки дороги: при достижении 40 пикселей — сброс
        self.road_offset += self.road_speed
        if self.road_offset >= 40:
            self.road_offset = 0

        self.distance += self.road_speed * 0.8   # Наращиваем пройденную дистанцию

        # Очки: монеты × 10 + дистанция × 0.5 + бонусы за щит и починку
        self.score = int(
            self.coins * 10
            + self.distance * 0.5
            + (100 if self.shield_active else 0)
            + self.repair_count * 40
        )

        # ── Интервалы спауна (уменьшаются с ростом уровня) ───────────────────
        traffic_interval  = max(28,  int(70  / diff["traffic_mul"]  - level * 2))
        obstacle_interval = max(35,  int(90  / diff["obstacle_mul"] - level * 2))
        powerup_interval  = 260
        event_interval    = max(180, 360 - level * 8)

        # Увеличиваем таймеры и при достижении порога — спауним объекты
        self.spawn_traffic_timer  += 1
        self.spawn_obstacle_timer += 1
        self.spawn_powerup_timer  += 1
        self.spawn_event_timer    += 1

        if self.spawn_traffic_timer >= traffic_interval:
            self.spawn_traffic_timer = 0
            if random.random() < 0.7:
                self.spawn_traffic()

        if self.spawn_obstacle_timer >= obstacle_interval:
            self.spawn_obstacle_timer = 0
            if random.random() < 0.75:
                self.spawn_obstacle()

        if self.spawn_powerup_timer >= powerup_interval:
            self.spawn_powerup_timer = 0
            if random.random() < 0.7:
                self.spawn_powerup()

        if self.spawn_event_timer >= event_interval:
            self.spawn_event_timer = 0
            if random.random() < 0.8:
                self.spawn_event()

        self.player.update()

        # ── Обновление и удаление объектов, вышедших за экран ────────────────
        for car in self.traffic[:]:
            car.update(self.road_speed)
            if car.y > HEIGHT + 100:
                self.traffic.remove(car)

        for obs in self.obstacles[:]:
            obs.update(self.road_speed)
            if obs.y > HEIGHT + 100:
                self.obstacles.remove(obs)

        for p in self.powerups[:]:
            p.update(self.road_speed)
            if p.y > HEIGHT + 100 or p.expired():
                self.powerups.remove(p)

        for e in self.road_events[:]:
            e.update(self.road_speed)
            if e.y > HEIGHT + 120:
                self.road_events.remove(e)

        # ── Коллизии с транспортными машинами ────────────────────────────────
        for car in self.traffic[:]:
            if self.player.rect.colliderect(car.rect):
                crashed = self.handle_crash(car)
                if not crashed and car in self.traffic:
                    self.traffic.remove(car)   # Убираем машину, если щит/починка поглотили удар

        # ── Коллизии с препятствиями ──────────────────────────────────────────
        for obs in self.obstacles[:]:
            if self.player.rect.colliderect(obs.rect):
                if obs.kind == "barrier":
                    # Барьер вызывает аварию
                    crashed = self.handle_crash(obs)
                    if not crashed and obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "oil":
                    # Масло вызывает случайный дрейф на соседнюю полосу
                    if self.player.move_cooldown == 0:
                        if random.choice([True, False]) and self.player.lane > 0:
                            self.player.move_left()
                        elif self.player.lane < LANE_COUNT - 1:
                            self.player.move_right()
                        self.player.move_cooldown = 18
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "pothole":
                    # Выбоина замедляет на 50 кадров
                    self.slow_timer = max(self.slow_timer, 50)
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "slow_zone":
                    # Зона замедления — 90 кадров
                    self.slow_timer = max(self.slow_timer, 90)
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)

        # ── Коллизии с бонусами ───────────────────────────────────────────────
        for p in self.powerups[:]:
            if self.player.rect.colliderect(p.rect):
                self.apply_powerup(p.type)
                # Начисляем дополнительные очки за подбор нитро и щита
                if p.type == "nitro":
                    self.score += 35
                elif p.type == "shield":
                    self.score += 50
                if p in self.powerups:
                    self.powerups.remove(p)

        # ── Коллизии с дорожными событиями ───────────────────────────────────
        for e in self.road_events[:]:
            if self.player.rect.colliderect(e.rect):
                if e.type == "moving_barrier":
                    crashed = self.handle_crash(e)
                    if not crashed and e in self.road_events:
                        self.road_events.remove(e)
                elif e.type == "speed_bump":
                    # Лежачий полицейский замедляет на 40 кадров
                    self.slow_timer = max(self.slow_timer, 40)
                elif e.type == "nitro_strip":
                    # Нитро-полоса даёт буст на 3 секунды (если нет активного бонуса)
                    if self.active_powerup is None:
                        self.active_powerup   = "nitro"
                        self.powerup_end_time = pygame.time.get_ticks() + 3000

        # ── Проверка финиша ───────────────────────────────────────────────────
        if self.distance >= FINISH_DISTANCE:
            self.state     = STATE_GAME_OVER
            self.game_over = True

        # ── Сохранение результата в таблицу рекордов (однократно) ────────────
        if self.state == STATE_GAME_OVER and not self.leaderboard_saved:
            add_score_to_leaderboard(
                self.username if self.username.strip() else "Player",
                self.score, self.distance, self.coins
            )
            self.leaderboard_saved = True

    def draw_road(self):
        """Отрисовывает фон, асфальт и анимированную дорожную разметку."""
        SCREEN.fill(BG)
        pygame.draw.rect(SCREEN, ROAD, (ROAD_MARGIN, 0, ROAD_WIDTH, HEIGHT))
        # Боковые белые полосы-ограничители
        pygame.draw.rect(SCREEN, WHITE, (ROAD_MARGIN - 4, 0, 4, HEIGHT))
        pygame.draw.rect(SCREEN, WHITE, (ROAD_MARGIN + ROAD_WIDTH, 0, 4, HEIGHT))

        # Пунктирная разметка между полосами; road_offset создаёт эффект движения
        for i in range(1, LANE_COUNT):
            x = ROAD_MARGIN + i * LANE_WIDTH
            for y in range(-40, HEIGHT, 80):
                pygame.draw.rect(SCREEN, ROAD_LINE,
                                 (x - 4, y + int(self.road_offset), 8, 40), border_radius=3)

    def draw_hud(self):
        """Рисует HUD: левая панель (игрок, очки, монеты, дистанция)
        и правая панель (активные бонусы)."""
        remaining = max(0, int(FINISH_DISTANCE - self.distance))

        # ── Левая панель ──────────────────────────────────────────────────────
        pygame.draw.rect(SCREEN, (0, 0, 0), (8, 8, 220, 132), border_radius=12)
        pygame.draw.rect(SCREEN, WHITE,     (8, 8, 220, 132), 2, border_radius=12)
        draw_text(f"Player: {self.username if self.username else 'Player'}", FONT_TINY,  WHITE, SCREEN, 18, 16)
        draw_text(f"Score: {int(self.score)}",        FONT_SMALL, WHITE, SCREEN, 18, 34)
        draw_text(f"Coins: {self.coins}",             FONT_SMALL, WHITE, SCREEN, 18, 58)
        draw_text(f"Distance: {int(self.distance)}",  FONT_SMALL, WHITE, SCREEN, 18, 82)
        draw_text(f"Remaining: {remaining}",          FONT_TINY,  WHITE, SCREEN, 18, 108)

        # ── Правая панель (бонусы) ────────────────────────────────────────────
        pygame.draw.rect(SCREEN, (0, 0, 0), (250, 8, 222, 132), border_radius=12)
        pygame.draw.rect(SCREEN, WHITE,     (250, 8, 222, 132), 2, border_radius=12)

        # Формируем строку активного бонуса с оставшимся временем нитро
        active_text = "None"
        if self.active_powerup == "nitro":
            remain      = max(0, (self.powerup_end_time - pygame.time.get_ticks()) // 1000 + 1)
            active_text = f"Nitro ({remain}s)"
        elif self.shield_active:
            active_text = "Shield"
        elif self.repair_count > 0:
            active_text = f"Repair x{self.repair_count}"

        draw_text("Power-Ups",                              FONT_SMALL, WHITE, SCREEN, 260, 20)
        draw_text(f"Active: {active_text}",                FONT_TINY,  WHITE, SCREEN, 260, 50)
        draw_text(f"Shield: {'ON' if self.shield_active else 'OFF'}", FONT_TINY, WHITE, SCREEN, 260, 76)
        draw_text(f"Repair: {self.repair_count}",          FONT_TINY,  WHITE, SCREEN, 260, 100)

    # ── Методы отрисовки экранов ──────────────────────────────────────────────

    def draw_main_menu(self):
        """Рисует главное меню с названием игры и кнопками навигации."""
        SCREEN.fill((25, 25, 35))
        draw_text("RACER GAME", FONT_BIG, WHITE,  SCREEN, WIDTH // 2, 120, center=True)
        draw_text("TSIS 3",     FONT_MED, YELLOW, SCREEN, WIDTH // 2, 170, center=True)
        for btn in self.menu_buttons:
            btn.draw(SCREEN)

    def draw_username_screen(self):
        """Рисует экран ввода имени игрока с текстовым полем и кнопкой Back."""
        SCREEN.fill((25, 25, 35))
        draw_text("Enter Username", FONT_BIG, WHITE, SCREEN, WIDTH // 2, 170, center=True)
        box = pygame.Rect(WIDTH // 2 - 150, 280, 300, 56)
        pygame.draw.rect(SCREEN, WHITE, box, border_radius=10)
        pygame.draw.rect(SCREEN, BLACK, box.inflate(-4, -4), border_radius=10)
        # Показываем введённый текст или подсказку
        draw_text(self.username if self.username else "Type your name...",
                  FONT_SMALL, WHITE, SCREEN, box.x + 12, box.y + 15)
        draw_text("Press ENTER to start", FONT_SMALL, LIGHT_GRAY, SCREEN, WIDTH // 2, 390, center=True)
        self.back_button.draw(SCREEN)

    def draw_settings(self):
        """Рисует экран настроек с актуальными значениями на кнопках."""
        SCREEN.fill((30, 30, 40))
        draw_text("Settings", FONT_BIG, WHITE, SCREEN, WIDTH // 2, 120, center=True)

        # Динамически обновляем надписи кнопок перед отрисовкой
        self.sound_button.text = f"Sound: {'On' if self.settings['sound'] else 'Off'}"
        self.color_button.text = f"Car Color: {self.settings['car_color'].title()}"
        self.diff_button.text  = f"Difficulty: {self.settings['difficulty'].title()}"

        self.sound_button.draw(SCREEN)
        self.color_button.draw(SCREEN)
        self.diff_button.draw(SCREEN)
        self.settings_back_button.draw(SCREEN)

    def draw_leaderboard(self):
        """Рисует таблицу рекордов: заголовки, топ-10 записей и кнопку Back."""
        SCREEN.fill((20, 30, 40))
        draw_text("Top 10 Leaderboard", FONT_MED, WHITE, SCREEN, WIDTH // 2, 60, center=True)
        data = load_leaderboard()

        headers     = ["#", "Name", "Score", "Dist"]
        x_positions = [35, 90, 250, 365]
        for i, h in enumerate(headers):
            draw_text(h, FONT_SMALL, YELLOW, SCREEN, x_positions[i], 110)

        y = 150
        if not data:
            draw_text("No scores yet", FONT_MED, LIGHT_GRAY, SCREEN, WIDTH // 2, HEIGHT // 2, center=True)
        else:
            for idx, item in enumerate(data, start=1):
                draw_text(str(idx),            FONT_SMALL, WHITE, SCREEN, x_positions[0], y)
                draw_text(item["name"][:10],   FONT_SMALL, WHITE, SCREEN, x_positions[1], y)  # Имя обрезается до 10 символов
                draw_text(str(item["score"]),  FONT_SMALL, WHITE, SCREEN, x_positions[2], y)
                draw_text(str(item["distance"]), FONT_SMALL, WHITE, SCREEN, x_positions[3], y)
                y += 42

        self.back_button.draw(SCREEN)

    def draw_game_over(self):
        """Рисует экран окончания игры: результаты и кнопки Retry / Main Menu.
        Заголовок меняется на 'FINISH!' при достижении финиша."""
        SCREEN.fill((30, 10, 10))
        title = "FINISH!" if self.distance >= FINISH_DISTANCE else "GAME OVER"
        draw_text(title,                                              FONT_BIG,   WHITE,  SCREEN, WIDTH // 2, 150, center=True)
        draw_text(f"Player: {self.username if self.username else 'Player'}", FONT_MED, YELLOW, SCREEN, WIDTH // 2, 240, center=True)
        draw_text(f"Score: {int(self.score)}",      FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 300, center=True)
        draw_text(f"Distance: {int(self.distance)}", FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 340, center=True)
        draw_text(f"Coins: {self.coins}",            FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 380, center=True)
        self.retry_button.draw(SCREEN)
        self.main_menu_button.draw(SCREEN)

    def draw_playing(self):
        """Рисует игровую сцену: дорогу, события, транспорт, препятствия,
        бонусы, машину игрока и HUD."""
        self.draw_road()
        for e in self.road_events:
            e.draw(SCREEN)
        for car in self.traffic:
            car.draw(SCREEN)
        for obs in self.obstacles:
            obs.draw(SCREEN)
        for p in self.powerups:
            p.draw(SCREEN)
        self.player.draw(SCREEN)
        self.draw_hud()

    # ── Обработчики событий для каждого состояния ─────────────────────────────

    def handle_main_menu_events(self, event):
        """Обрабатывает клики по кнопкам главного меню."""
        if self.menu_buttons[0].clicked(event):
            self.state = STATE_USERNAME
        elif self.menu_buttons[1].clicked(event):
            self.state = STATE_LEADERBOARD
        elif self.menu_buttons[2].clicked(event):
            self.state = STATE_SETTINGS
        elif self.menu_buttons[3].clicked(event):
            self.running = False

    def handle_username_events(self, event):
        """Обрабатывает ввод имени пользователя с клавиатуры.
        Enter — начать игру, Backspace — удалить последний символ."""
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if not self.username.strip():
                    self.username = "Player"   # Имя по умолчанию
                self.start_run()
                self.state = STATE_PLAYING
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            else:
                # Допускаем только печатаемые символы; ограничение — 12 знаков
                if len(self.username) < 12 and event.unicode.isprintable():
                    self.username += event.unicode

    def handle_settings_events(self, event):
        """Обрабатывает изменение настроек: звук (toggle), цвет машины
        и сложность (циклическое переключение). Каждое изменение сохраняется."""
        if self.sound_button.clicked(event):
            self.settings["sound"] = not self.settings["sound"]
            save_settings(self.settings)

        elif self.color_button.clicked(event):
            colors = list(CAR_COLORS.keys())
            idx    = colors.index(self.settings["car_color"])
            self.settings["car_color"] = colors[(idx + 1) % len(colors)]
            save_settings(self.settings)

        elif self.diff_button.clicked(event):
            diffs = list(DIFFICULTY_PRESETS.keys())
            idx   = diffs.index(self.settings["difficulty"])
            self.settings["difficulty"] = diffs[(idx + 1) % len(diffs)]
            save_settings(self.settings)

        elif self.settings_back_button.clicked(event):
            # При возврате применяем новый цвет к машине игрока
            self.player.set_color(self.settings["car_color"])
            self.state = STATE_MAIN_MENU

    def handle_leaderboard_events(self, event):
        """Обрабатывает нажатие кнопки Back на экране таблицы рекордов."""
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

    def handle_game_over_events(self, event):
        """Обрабатывает кнопки Retry и Main Menu на экране окончания игры."""
        if self.retry_button.clicked(event):
            self.start_run()
            self.state = STATE_PLAYING
        elif self.main_menu_button.clicked(event):
            self.state = STATE_MAIN_MENU

    def handle_playing_events(self, event):
        """Обрабатывает управление во время игры:
        ← / → — смена полосы (с кулдауном), Escape — выход в главное меню."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and self.player.move_cooldown == 0:
                self.player.move_left()
                self.player.move_cooldown = 8
            elif event.key == pygame.K_RIGHT and self.player.move_cooldown == 0:
                self.player.move_right()
                self.player.move_cooldown = 8
            elif event.key == pygame.K_ESCAPE:
                self.state = STATE_MAIN_MENU

    def events(self):
        """Главный диспетчер событий: перехватывает pygame.QUIT
        и направляет остальные события в обработчик текущего состояния."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.state == STATE_MAIN_MENU:
                self.handle_main_menu_events(event)
            elif self.state == STATE_USERNAME:
                self.handle_username_events(event)
            elif self.state == STATE_SETTINGS:
                self.handle_settings_events(event)
            elif self.state == STATE_LEADERBOARD:
                self.handle_leaderboard_events(event)
            elif self.state == STATE_PLAYING:
                self.handle_playing_events(event)
            elif self.state == STATE_GAME_OVER:
                self.handle_game_over_events(event)

    def update(self):
        """Запускает игровую логику только в состоянии STATE_PLAYING."""
        if self.state == STATE_PLAYING:
            self.update_playing()

    def draw(self):
        """Выбирает и вызывает метод отрисовки в зависимости от текущего состояния."""
        if self.state == STATE_MAIN_MENU:
            self.draw_main_menu()
        elif self.state == STATE_USERNAME:
            self.draw_username_screen()
        elif self.state == STATE_SETTINGS:
            self.draw_settings()
        elif self.state == STATE_LEADERBOARD:
            self.draw_leaderboard()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()   # Обновляем экран после полной отрисовки кадра

    def run(self):
        """Главный игровой цикл: ограничивает FPS, обрабатывает события,
        обновляет логику и рисует кадр. Завершает работу при running=False."""
        while self.running:
            CLOCK.tick(FPS)   # Ограничиваем частоту до 60 FPS
            self.events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()


# ── Точка входа ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()