# game.py — Логика Snake Game: движение змейки, еда, яд, пауэрапы, препятствия, отрисовка

import pygame, random
from config import *  # Константы: COLS, ROWS, CELL, цвета, FPS_DEFAULT и т.д.

# Словарь направлений: название → вектор (dx, dy) в клетках
DIRECTIONS = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0)}

# Противоположные направления — для запрета разворота на 180°
OPPOSITE   = {"UP":"DOWN", "DOWN":"UP", "LEFT":"RIGHT", "RIGHT":"LEFT"}

# Типы еды: (название, цвет, очки за съедение, TTL в секундах; 0 = не исчезает)
FOOD_TYPES = [
    ("normal", FOOD_NORM,   1, 0),   # Обычная еда — постоянная, +1 очко
    ("bonus",  FOOD_BONUS,  3, 8),   # Бонусная — исчезает через 8 с, +3 очка
    ("rare",   FOOD_RARE,   5, 5),   # Редкая — исчезает через 5 с, +5 очков
    ("poison", FOOD_POISON, 0, 0),   # Яд — укорачивает змейку на 3 сегмента, -2 очка
]

# Типы пауэрапов
POWERUP_TYPES  = ["speed", "slow", "shield"]

# Цвета пауэрапов (из config.py)
PU_COLORS      = {"speed": PU_SPEED, "slow": PU_SLOW, "shield": PU_SHIELD}

# Длительность эффекта каждого пауэрапа в мс; 0 = до срабатывания (щит)
PU_DURATION_MS = {"speed": 5000, "slow": 5000, "shield": 0}

# Время жизни пауэрапа на поле (8 секунд), после чего он исчезает несобранным
PU_FIELD_TTL   = 8000


class SnakeGame:
    """
    Содержит всю игровую логику: состояние змейки, еду, пауэрапы, препятствия,
    уровни и отрисовку игрового поля + HUD.
    """

    def __init__(self, settings, username, personal_best):
        self.settings      = settings
        self.username      = username
        self.personal_best = personal_best
        self.snake_color   = tuple(settings["snake_color"])  # RGB-цвет тела змейки
        self.grid          = settings["grid_overlay"]        # Показывать ли сетку

        # Начальная позиция змейки — горизонтально по центру поля, длина 3
        cx, cy = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx-1, cy), (cx-2, cy)]
        self.direction = "RIGHT"   # Текущее направление (зафиксированное)
        self.next_dir  = "RIGHT"   # Следующее направление (от игрока, применяется в update)

        # Игровые счётчики
        self.score       = 0
        self.level       = 1
        self.food_eaten  = 0        # Сброс при переходе на новый уровень
        self.food_per_level = 5     # Еды для перехода на следующий уровень

        # Состояние окончания игры
        self.game_over        = False
        self.game_over_reason = ""

        # Базовая скорость; увеличивается с уровнем (см. _advance_level)
        self.fps = FPS_DEFAULT

        # Тайм-метки окончания эффектов пауэрапов (в мс, pygame.time.get_ticks())
        self.speed_boost_end = 0
        self.slow_end        = 0

        # Состояние щита и метка активного пауэрапа для HUD
        self.shield_active       = False
        self.active_powerup_label = None

        # Списки объектов на поле
        self.foods    = []          # Список словарей с данными о каждом куске еды
        self.powerup  = None        # Текущий пауэрап (только один на поле)
        self.pu_spawn_time = 0      # Время появления пауэрапа (для TTL)
        self.obstacles = set()      # Множество (x,y) клеток со стенами-препятствиями

        # Размещаем начальную еду и пауэрап принудительно (force=True)
        self._place_food()
        self._maybe_place_powerup(force=True)

    # ──────────────────────────────────────────────
    # Вспомогательные методы размещения объектов
    # ──────────────────────────────────────────────

    def _free_cells(self, extra=None):
        """
        Возвращает список свободных клеток поля (не занятых телом змейки,
        препятствиями и переданными дополнительными позициями).
        """
        occ = set(self.body) | self.obstacles
        if extra:
            occ |= set(extra)
        return [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occ]

    def _place_food(self):
        """
        Добавляет новый кусок еды, если на поле меньше 2 штук.
        Тип выбирается случайно с весами [4:2:1:1] (обычная:бонус:редкая:яд).
        Еда с TTL>0 получает время истечения; TTL=0 — постоянная.
        """
        if len(self.foods) >= 2:
            return
        # Исключаем клетки с уже существующей едой
        free = self._free_cells([(f["x"], f["y"]) for f in self.foods])
        if not free:
            return
        # Взвешенный случайный выбор типа еды
        ftype = random.choices(FOOD_TYPES, [4, 2, 1, 1], k=1)[0]
        name, color, pts, ttl = ftype
        pos = random.choice(free)
        self.foods.append({
            "x": pos[0], "y": pos[1],
            "type": name, "color": color, "pts": pts,
            "expires": pygame.time.get_ticks() + ttl * 1000 if ttl > 0 else 0,
            "ttl": ttl
        })

    def _maybe_place_powerup(self, force=False):
        """
        Пытается разместить пауэрап на поле. При force=True — гарантированно.
        Иначе — с вероятностью 25%. На поле одновременно не более одного пауэрапа.
        """
        if self.powerup:
            return  # Уже есть пауэрап — не спавним второй
        if not force and random.random() > 0.25:
            return  # 75% шанс пропустить спавн
        # Исключаем клетки с едой при выборе позиции
        fc = [(f["x"], f["y"]) for f in self.foods]
        free = self._free_cells(fc)
        if not free:
            return
        ptype = random.choice(POWERUP_TYPES)
        pos = random.choice(free)
        self.powerup      = {"x": pos[0], "y": pos[1], "type": ptype}
        self.pu_spawn_time = pygame.time.get_ticks()

    def _place_obstacles(self):
        """
        Добавляет препятствия начиная с Level 3.
        Количество: 2 + (level-3)*2 (растёт с уровнем).
        Зона 7×7 вокруг головы змейки защищена — туда блоки не ставятся.
        Препятствия не появляются на клетках с едой или телом змейки.
        """
        if self.level < 3:
            return
        count = 2 + (self.level - 3) * 2
        head  = self.body[0]
        # «Безопасная зона» вокруг головы радиусом 3 клетки
        safety = {(head[0]+dx, head[1]+dy) for dx in range(-3, 4) for dy in range(-3, 4)}
        cands = [
            (x, y) for x in range(COLS) for y in range(ROWS)
            if (x, y) not in set(self.body)
            and (x, y) not in self.obstacles
            and (x, y) not in safety
            and not any(f["x"] == x and f["y"] == y for f in self.foods)
        ]
        random.shuffle(cands)
        for pos in cands[:count]:
            self.obstacles.add(pos)

    def _advance_level(self):
        """
        Повышает уровень: сбрасывает счётчик еды, увеличивает базовую скорость
        (до максимума 22 FPS) и добавляет новые препятствия.
        """
        self.level      += 1
        self.food_eaten  = 0
        self.fps = min(FPS_DEFAULT + (self.level - 1) * 2, 22)
        self._place_obstacles()

    # ──────────────────────────────────────────────
    # Свойство текущей скорости (с учётом пауэрапов)
    # ──────────────────────────────────────────────

    @property
    def current_fps(self):
        """
        Возвращает эффективный FPS с учётом активных пауэрапов:
        - Speed Boost: +6 FPS (макс. 28)
        - Slow Motion: -4 FPS (мин. 3)
        - Без пауэрапа: базовый fps уровня
        """
        now = pygame.time.get_ticks()
        if now < self.speed_boost_end: return min(self.fps + 6, 28)
        if now < self.slow_end:        return max(self.fps - 4, 3)
        return self.fps

    def change_direction(self, d):
        """Устанавливает следующее направление, запрещая разворот на 180°."""
        if d != OPPOSITE[self.direction]:
            self.next_dir = d

    # ──────────────────────────────────────────────
    # Основной игровой тик
    # ──────────────────────────────────────────────

    def update(self):
        """
        Один шаг игровой логики (вызывается из App._update с фиксированным интервалом):
        1. Удаляем просроченную еду; пополняем если нужно.
        2. Удаляем пауэрап если истёк TTL на поле.
        3. Сбрасываем метки истёкших пауэрап-эффектов.
        4. Двигаем змейку в новом направлении.
        5. Проверяем столкновения (стена / препятствие / сама себя).
        6. Обрабатываем поедание еды (яд или обычная) и сбор пауэрапа.
        """
        if self.game_over:
            return

        now = pygame.time.get_ticks()

        # Удаляем еду с истёкшим временем жизни (expires>0 и время прошло)
        self.foods = [f for f in self.foods if f["expires"] == 0 or now < f["expires"]]
        if not self.foods:
            self._place_food()

        # Убираем пауэрап с поля если он пролежал дольше PU_FIELD_TTL
        if self.powerup and (now - self.pu_spawn_time) > PU_FIELD_TTL:
            self.powerup = None

        # Снимаем метки эффектов Speed/Slow после истечения их длительности
        if self.active_powerup_label == "speed" and now >= self.speed_boost_end:
            self.active_powerup_label = None
        if self.active_powerup_label == "slow" and now >= self.slow_end:
            self.active_powerup_label = None

        # Фиксируем направление (next_dir устанавливается обработчиком событий)
        self.direction = self.next_dir
        dx, dy = DIRECTIONS[self.direction]
        hx, hy = self.body[0]
        nh = (hx + dx, hy + dy)  # Новая позиция головы

        # Определяем тип столкновения
        wall  = not (0 <= nh[0] < COLS and 0 <= nh[1] < ROWS)
        self_ = nh in self.body[:-1]   # Хвост исключён — голова могла бы зайти
        obs_  = nh in self.obstacles

        if wall or self_ or obs_:
            if self.shield_active:
                # Щит поглощает одно столкновение и деактивируется
                self.shield_active        = False
                self.active_powerup_label = None
                return
            # Игра окончена — фиксируем причину
            self.game_over = True
            self.game_over_reason = (
                "Hit the wall!"      if wall  else
                "Hit an obstacle!"   if obs_  else
                "Bit yourself!"
            )
            return

        # Добавляем новую голову
        self.body.insert(0, nh)

        # Проверяем, съела ли змейка еду
        ate = False
        for food in self.foods[:]:
            if nh == (food["x"], food["y"]):
                if food["type"] == "poison":
                    # Яд: укорачиваем на 3 сегмента, -2 очка
                    for _ in range(3):
                        if len(self.body) > 1:
                            self.body.pop()
                    if len(self.body) <= 1:
                        # Змейка слишком короткая — game over
                        self.game_over = True
                        self.game_over_reason = "Poisoned!"
                        return
                    self.score = max(0, self.score - 2)
                else:
                    # Обычная/бонусная/редкая: добавляем очки, проверяем смену уровня
                    self.score      += food["pts"]
                    self.food_eaten += 1
                    if self.food_eaten >= self.food_per_level:
                        self._advance_level()
                self.foods.remove(food)
                self._place_food()
                self._maybe_place_powerup()
                ate = True
                break

        if not ate:
            # Еда не съедена — убираем хвост (обычное движение)
            self.body.pop()

        # Проверяем, собрала ли голова пауэрап
        if self.powerup and nh == (self.powerup["x"], self.powerup["y"]):
            pt = self.powerup["type"]
            if pt == "speed":
                self.speed_boost_end      = now + 5000
                self.active_powerup_label = "speed"
            elif pt == "slow":
                self.slow_end             = now + 5000
                self.active_powerup_label = "slow"
            elif pt == "shield":
                self.shield_active        = True
                self.active_powerup_label = "shield"
            self.powerup = None  # Пауэрап собран — убираем с поля

    # ──────────────────────────────────────────────
    # Отрисовка игрового поля
    # ──────────────────────────────────────────────

    def draw(self, surface):
        """
        Отрисовывает игровую область (ниже HUD-полосы высотой 80 px):
        фон → сетка → препятствия → еда → пауэрап → тело змейки → рамка поля.
        """
        # Фон игровой зоны
        pygame.draw.rect(surface, BG, (0, 80, WIDTH, HEIGHT - 80))

        # Опциональная клеточная сетка
        if self.grid:
            for x in range(COLS):
                for y in range(ROWS):
                    pygame.draw.rect(surface, GRID_COLOR, (x*CELL, 80+y*CELL, CELL, CELL), 1)

        # Препятствия — тёмные закруглённые прямоугольники
        for ox, oy in self.obstacles:
            pygame.draw.rect(surface, OBSTACLE,
                             (ox*CELL+2, 80+oy*CELL+2, CELL-4, CELL-4), border_radius=4)

        # Еда — эллипсы; с таймером — белая полоска убывающего времени снизу
        for food in self.foods:
            r = pygame.Rect(food["x"]*CELL+4, 80+food["y"]*CELL+4, CELL-8, CELL-8)
            pygame.draw.ellipse(surface, food["color"], r)
            if food["expires"] > 0:
                # Полоска TTL: ширина пропорциональна оставшемуся времени
                now   = pygame.time.get_ticks()
                ratio = max(0, (food["expires"] - now) / (food["ttl"] * 1000))
                bw    = int((CELL - 8) * ratio)
                pygame.draw.rect(surface, WHITE,
                                 (food["x"]*CELL+4, 80+food["y"]*CELL+CELL-8, bw, 4))

        # Пауэрап — цветной прямоугольник с белой рамкой
        if self.powerup:
            px, py = self.powerup["x"], self.powerup["y"]
            r = pygame.Rect(px*CELL+3, 80+py*CELL+3, CELL-6, CELL-6)
            pygame.draw.rect(surface, PU_COLORS[self.powerup["type"]], r, border_radius=6)
            pygame.draw.rect(surface, WHITE, r, 2, border_radius=6)

        # Тело змейки — закруглённые прямоугольники; щит меняет цвет на PU_SHIELD
        for i, (sx, sy) in enumerate(self.body):
            col = PU_SHIELD if self.shield_active else self.snake_color
            r   = pygame.Rect(sx*CELL+1, 80+sy*CELL+1, CELL-2, CELL-2)
            pygame.draw.rect(surface, col, r, border_radius=5)
            if i == 0:
                # Глаза головы — два чёрных кружка
                pygame.draw.circle(surface, BLACK, (sx*CELL+7,     80+sy*CELL+7), 3)
                pygame.draw.circle(surface, BLACK, (sx*CELL+CELL-7, 80+sy*CELL+7), 3)

        # Рамка игрового поля поверх всего
        pygame.draw.rect(surface, WALL, (0, 80, WIDTH, HEIGHT - 80), 4)

    # ──────────────────────────────────────────────
    # Отрисовка HUD (верхняя полоса 80 px)
    # ──────────────────────────────────────────────

    def draw_hud(self, surface, font_med, font_small):
        """
        HUD отображает: счёт, уровень, личный рекорд (слева);
        активный пауэрап с таймером (по центру);
        имя игрока и длина змейки (справа).
        """
        # Фон HUD-полосы и разделительная линия
        pygame.draw.rect(surface, HUD_BG, (0, 0, WIDTH, 80))
        pygame.draw.line(surface, WALL, (0, 80), (WIDTH, 80), 2)

        # Левая секция: счёт, уровень, рекорд
        _t(font_med,   f"Score: {self.score}",          WHITE,      surface, 14, 8)
        _t(font_small, f"Level: {self.level}",          LIGHT_GRAY, surface, 14, 42)
        _t(font_small, f"Best: {self.personal_best}",   LIGHT_GRAY, surface, 14, 60)

        # Центральная секция: активный пауэрап с обратным отсчётом
        now = pygame.time.get_ticks()
        if self.active_powerup_label == "speed":
            rem = max(0, (self.speed_boost_end - now) // 1000 + 1)
            _t(font_small, f"SPEED BOOST ({rem}s)", PU_SPEED,  surface, WIDTH//2, 10, center=True)
        elif self.active_powerup_label == "slow":
            rem = max(0, (self.slow_end - now) // 1000 + 1)
            _t(font_small, f"SLOW MOTION ({rem}s)", PU_SLOW,   surface, WIDTH//2, 10, center=True)
        elif self.shield_active:
            _t(font_small, "SHIELD ACTIVE",          PU_SHIELD, surface, WIDTH//2, 10, center=True)

        # Правая секция: имя игрока и длина змейки
        _t(font_small, self.username,          LIGHT_GRAY, surface, WIDTH-14, 8,  right=True)
        _t(font_small, f"Length: {len(self.body)}", LIGHT_GRAY, surface, WIDTH-14, 30, right=True)


# ──────────────────────────────────────────────
# Вспомогательная функция отрисовки текста
# ──────────────────────────────────────────────

def _t(font, text, color, surface, x, y, center=False, right=False):
    """
    Рисует текст на поверхности с гибким выравниванием:
    - center=True  → горизонтально по центру (midtop)
    - right=True   → выровнен по правому краю (topright)
    - иначе        → левый верхний угол (topleft)
    """
    img = font.render(str(text), True, color)
    r   = img.get_rect()
    if center:  r.midtop   = (x, y)
    elif right: r.topright = (x, y)
    else:       r.topleft  = (x, y)
    surface.blit(img, r)