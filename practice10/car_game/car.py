import pygame
import random
import json
import os
import sys
from datetime import datetime

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 480, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSIS 3 Racer Game")
CLOCK = pygame.time.Clock()
FPS = 60

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (120, 120, 120)
LIGHT_GRAY = (200, 200, 200)
RED = (220, 60, 60)
GREEN = (60, 200, 100)
BLUE = (70, 140, 255)
YELLOW = (240, 210, 70)
ORANGE = (255, 150, 50)
PURPLE = (170, 90, 220)
CYAN = (70, 220, 220)
BG = (35, 35, 35)
ROAD = (70, 70, 70)
ROAD_LINE = (240, 240, 240)
BARRIER = (190, 80, 80)
OIL = (30, 30, 30)
POTHOLE = (100, 70, 50)
SLOW = (80, 140, 255)

FONT_BIG = pygame.font.SysFont("arial", 42, bold=True)
FONT_MED = pygame.font.SysFont("arial", 28, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 20)
FONT_TINY = pygame.font.SysFont("arial", 16)

SETTINGS_FILE = "settings.json"
LEADERBOARD_FILE = "leaderboard.json"

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "red",
    "difficulty": "normal"
}

DIFFICULTY_PRESETS = {
    "easy": {"speed_mul": 0.9, "traffic_mul": 0.8, "obstacle_mul": 0.8},
    "normal": {"speed_mul": 1.0, "traffic_mul": 1.0, "obstacle_mul": 1.0},
    "hard": {"speed_mul": 1.15, "traffic_mul": 1.2, "obstacle_mul": 1.25},
}

CAR_COLORS = {
    "red": RED,
    "blue": BLUE,
    "green": GREEN,
    "yellow": YELLOW
}

STATE_MAIN_MENU = "MAIN_MENU"
STATE_USERNAME = "USERNAME"
STATE_SETTINGS = "SETTINGS"
STATE_LEADERBOARD = "LEADERBOARD"
STATE_PLAYING = "PLAYING"
STATE_GAME_OVER = "GAME_OVER"

LANE_COUNT = 3
ROAD_MARGIN = 70
ROAD_WIDTH = WIDTH - ROAD_MARGIN * 2
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT
LANE_X = [ROAD_MARGIN + i * LANE_WIDTH + LANE_WIDTH // 2 for i in range(LANE_COUNT)]

FINISH_DISTANCE = 5000
SAFE_SPAWN_DISTANCE = 260
MIN_VERTICAL_GAP = 130


def load_json(path, default_data):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4)
        return default_data


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_settings():
    return load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)


def load_leaderboard():
    return load_json(LEADERBOARD_FILE, [])


def save_leaderboard(entries):
    save_json(LEADERBOARD_FILE, entries)


def add_score_to_leaderboard(name, score, distance, coins):
    data = load_leaderboard()
    data.append({
        "name": name,
        "score": int(score),
        "distance": int(distance),
        "coins": int(coins),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    data.sort(key=lambda x: (x["score"], x["distance"]), reverse=True)
    data = data[:10]
    save_leaderboard(data)


def draw_text(text, font, color, surface, x, y, center=False):
    img = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)


class Button:
    def __init__(self, x, y, w, h, text, bg=GRAY, hover=LIGHT_GRAY, fg=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg = bg
        self.hover = hover
        self.fg = fg

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()
        color = self.hover if self.rect.collidepoint(mouse) else self.bg
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=12)
        draw_text(self.text, FONT_SMALL, self.fg, surface, self.rect.centerx, self.rect.centery, center=True)

    def clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)


class PlayerCar:
    def __init__(self, color_name):
        self.width = 48
        self.height = 88
        self.lane = 1
        self.x = LANE_X[self.lane] - self.width // 2
        self.y = HEIGHT - 130
        self.color_name = color_name
        self.color = CAR_COLORS[color_name]
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.move_cooldown = 0
        self.drift_timer = 0

    def set_color(self, color_name):
        self.color_name = color_name
        self.color = CAR_COLORS[color_name]

    def move_left(self):
        if self.lane > 0:
            self.lane -= 1
            self.x = LANE_X[self.lane] - self.width // 2

    def move_right(self):
        if self.lane < LANE_COUNT - 1:
            self.lane += 1
            self.x = LANE_X[self.lane] - self.width // 2

    def update(self):
        self.rect.topleft = (self.x, self.y)
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
        if self.drift_timer > 0:
            self.drift_timer -= 1

    def draw(self, surface):
        body = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, body, border_radius=10)
        pygame.draw.rect(surface, WHITE, body, 2, border_radius=10)
        pygame.draw.rect(surface, CYAN, (self.x + 8, self.y + 10, self.width - 16, 18), border_radius=6)
        pygame.draw.circle(surface, BLACK, (self.x + 10, self.y + 16), 6)
        pygame.draw.circle(surface, BLACK, (self.x + self.width - 10, self.y + 16), 6)
        pygame.draw.circle(surface, BLACK, (self.x + 10, self.y + self.height - 14), 6)
        pygame.draw.circle(surface, BLACK, (self.x + self.width - 10, self.y + self.height - 14), 6)


class TrafficCar:
    def __init__(self, lane, speed):
        self.width = 46
        self.height = 84
        self.lane = lane
        self.x = LANE_X[lane] - self.width // 2
        self.y = -self.height - random.randint(20, 120)
        self.speed = speed
        self.color = random.choice([BLUE, GREEN, YELLOW, ORANGE, PURPLE])
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        pygame.draw.rect(surface, CYAN, (self.x + 8, self.y + 10, self.width - 16, 16), border_radius=5)


class Obstacle:
    def __init__(self, lane, kind, speed):
        self.lane = lane
        self.kind = kind
        self.speed = speed
        self.width = 52 if kind in ("barrier", "slow_zone") else 42
        self.height = 28 if kind in ("oil", "pothole") else 36
        self.x = LANE_X[lane] - self.width // 2
        self.y = -self.height - random.randint(20, 120)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        if self.kind == "barrier":
            pygame.draw.rect(surface, BARRIER, self.rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=6)
        elif self.kind == "oil":
            pygame.draw.ellipse(surface, OIL, self.rect)
            pygame.draw.ellipse(surface, LIGHT_GRAY, self.rect, 2)
        elif self.kind == "pothole":
            pygame.draw.ellipse(surface, POTHOLE, self.rect)
            pygame.draw.ellipse(surface, BLACK, self.rect, 2)
        elif self.kind == "slow_zone":
            pygame.draw.rect(surface, SLOW, self.rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=6)


class PowerUp:
    def __init__(self, lane, ptype, speed):
        self.lane = lane
        self.type = ptype
        self.speed = speed
        self.size = 28
        self.x = LANE_X[lane] - self.size // 2
        self.y = -self.size - random.randint(20, 120)
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        self.life_ms = 7000
        self.spawn_time = pygame.time.get_ticks()

    def update(self, road_speed):
        self.y += self.speed + road_speed
        self.rect.topleft = (self.x, self.y)

    def expired(self):
        return pygame.time.get_ticks() - self.spawn_time > self.life_ms

    def draw(self, surface):
        color = {"nitro": ORANGE, "shield": CYAN, "repair": GREEN}[self.type]
        pygame.draw.circle(surface, color, self.rect.center, self.size // 2)
        pygame.draw.circle(surface, WHITE, self.rect.center, self.size // 2, 2)
        label = {"nitro": "N", "shield": "S", "repair": "R"}[self.type]
        draw_text(label, FONT_SMALL, BLACK, surface, self.rect.centerx, self.rect.centery, center=True)


class RoadEvent:
    def __init__(self, etype, lane, speed):
        self.type = etype
        self.lane = lane
        self.speed = speed
        self.finished = False
        if etype == "moving_barrier":
            self.width = 50
            self.height = 26
            self.x = LANE_X[lane] - self.width // 2
            self.y = -60
            self.direction = random.choice([-1, 1])
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        elif etype == "speed_bump":
            self.width = LANE_WIDTH - 14
            self.height = 16
            self.x = LANE_X[lane] - self.width // 2
            self.y = -40
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        else:  # nitro_strip
            self.width = LANE_WIDTH - 18
            self.height = 70
            self.x = LANE_X[lane] - self.width // 2
            self.y = -100
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, road_speed):
        self.y += self.speed + road_speed
        if self.type == "moving_barrier":
            self.x += self.direction * 2.2
            left_limit = ROAD_MARGIN
            right_limit = ROAD_MARGIN + ROAD_WIDTH - self.width
            if self.x <= left_limit or self.x >= right_limit:
                self.direction *= -1
        self.rect.topleft = (self.x, self.y)

    def draw(self, surface):
        if self.type == "moving_barrier":
            pygame.draw.rect(surface, PURPLE, self.rect, border_radius=5)
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)
        elif self.type == "speed_bump":
            pygame.draw.rect(surface, YELLOW, self.rect, border_radius=4)
            pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=4)
        elif self.type == "nitro_strip":
            pygame.draw.rect(surface, ORANGE, self.rect, border_radius=4)
            for i in range(4):
                pygame.draw.line(surface, WHITE, (self.x + 6, self.y + 10 + i * 14), (self.x + self.width - 6, self.y + 10 + i * 14), 2)


class Game:
    def __init__(self):
        self.settings = load_settings()
        self.running = True
        self.state = STATE_MAIN_MENU
        self.username = ""
        self.road_offset = 0
        self.leaderboard_saved = False

        self.menu_buttons = [
            Button(WIDTH // 2 - 100, 260, 200, 55, "Play"),
            Button(WIDTH // 2 - 100, 330, 200, 55, "Leaderboard"),
            Button(WIDTH // 2 - 100, 400, 200, 55, "Settings"),
            Button(WIDTH // 2 - 100, 470, 200, 55, "Quit"),
        ]

        self.back_button = Button(20, 20, 110, 45, "Back")
        self.retry_button = Button(WIDTH // 2 - 100, 470, 200, 55, "Retry")
        self.main_menu_button = Button(WIDTH // 2 - 100, 540, 200, 55, "Main Menu")

        self.sound_button = Button(WIDTH // 2 - 100, 220, 200, 50, "")
        self.color_button = Button(WIDTH // 2 - 100, 300, 200, 50, "")
        self.diff_button = Button(WIDTH // 2 - 100, 380, 200, 50, "")
        self.settings_back_button = Button(WIDTH // 2 - 100, 470, 200, 55, "Back")

        self.start_run()

    def start_run(self):
        self.player = PlayerCar(self.settings["car_color"])
        self.score = 0
        self.coins = 0
        self.distance = 0
        self.base_speed = 5.0 * DIFFICULTY_PRESETS[self.settings["difficulty"]]["speed_mul"]
        self.road_speed = self.base_speed
        self.game_over = False
        self.shield_active = False
        self.repair_count = 0
        self.active_powerup = None
        self.powerup_end_time = 0
        self.slow_timer = 0
        self.traffic = []
        self.obstacles = []
        self.powerups = []
        self.road_events = []
        self.coin_items = []
        self.spawn_traffic_timer = 0
        self.spawn_obstacle_timer = 0
        self.spawn_powerup_timer = 0
        self.spawn_event_timer = 0
        self.leaderboard_saved = False

    def get_level(self):
        return 1 + int(self.distance // 500)

    def get_player_rect(self):
        return self.player.rect

    def can_spawn_lane(self, lane, new_y, objects):
        if lane == self.player.lane and new_y > -SAFE_SPAWN_DISTANCE:
            return False
        for obj in objects:
            if hasattr(obj, "lane") and obj.lane == lane and abs(obj.y - new_y) < MIN_VERTICAL_GAP:
                return False
        return True

    def choose_safe_lane(self, existing_objects):
        lanes = list(range(LANE_COUNT))
        random.shuffle(lanes)
        for lane in lanes:
            if self.can_spawn_lane(lane, -80, existing_objects):
                return lane
        return None

    def spawn_traffic(self):
        lane = self.choose_safe_lane(self.traffic + self.obstacles)
        if lane is not None:
            speed = random.uniform(1.0, 2.8) + self.get_level() * 0.15
            self.traffic.append(TrafficCar(lane, speed))

    def spawn_obstacle(self):
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
        lane = self.choose_safe_lane(self.traffic + self.obstacles + self.powerups)
        if lane is not None:
            ptype = random.choice(["nitro", "shield", "repair"])
            self.powerups.append(PowerUp(lane, ptype, 1.2))

    def spawn_event(self):
        etype = random.choice(["moving_barrier", "speed_bump", "nitro_strip"])
        lane = random.randint(0, LANE_COUNT - 1)
        self.road_events.append(RoadEvent(etype, lane, 1.2))

    def apply_powerup(self, ptype):
        if ptype == "repair":
            self.repair_count = min(1, self.repair_count + 1)
            self.score += 40
            return

        if self.active_powerup is not None:
            return

        self.active_powerup = ptype
        if ptype == "nitro":
            self.powerup_end_time = pygame.time.get_ticks() + random.randint(3000, 5000)
        elif ptype == "shield":
            self.shield_active = True
            self.powerup_end_time = 0

    def clear_active_powerup(self):
        if self.active_powerup == "nitro":
            self.road_speed = max(self.base_speed, self.road_speed)
        self.active_powerup = None

    def handle_crash(self, remove_obj=None):
        if self.shield_active:
            self.shield_active = False
            self.active_powerup = None
            self.score += 100
            return False
        if self.repair_count > 0:
            self.repair_count -= 1
            self.score += 50
            return False
        self.game_over = True
        self.state = STATE_GAME_OVER
        return True

    def update_playing(self):
        if self.game_over:
            return

        level = self.get_level()
        diff = DIFFICULTY_PRESETS[self.settings["difficulty"]]

        self.base_speed = (5.0 + level * 0.18) * diff["speed_mul"]
        self.road_speed = self.base_speed

        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.road_speed *= 0.65

        if self.active_powerup == "nitro":
            if pygame.time.get_ticks() < self.powerup_end_time:
                self.road_speed *= 1.75
            else:
                self.clear_active_powerup()

        self.road_offset += self.road_speed
        if self.road_offset >= 40:
            self.road_offset = 0

        self.distance += self.road_speed * 0.8
        self.score = int(self.coins * 10 + self.distance * 0.5 + (100 if self.shield_active else 0) + self.repair_count * 40)

        traffic_interval = max(28, int(70 / diff["traffic_mul"] - level * 2))
        obstacle_interval = max(35, int(90 / diff["obstacle_mul"] - level * 2))
        powerup_interval = 260
        event_interval = max(180, 360 - level * 8)

        self.spawn_traffic_timer += 1
        self.spawn_obstacle_timer += 1
        self.spawn_powerup_timer += 1
        self.spawn_event_timer += 1

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

        for car in self.traffic[:]:
            if self.player.rect.colliderect(car.rect):
                crashed = self.handle_crash(car)
                if not crashed and car in self.traffic:
                    self.traffic.remove(car)

        for obs in self.obstacles[:]:
            if self.player.rect.colliderect(obs.rect):
                if obs.kind == "barrier":
                    crashed = self.handle_crash(obs)
                    if not crashed and obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "oil":
                    if self.player.move_cooldown == 0:
                        if random.choice([True, False]) and self.player.lane > 0:
                            self.player.move_left()
                        elif self.player.lane < LANE_COUNT - 1:
                            self.player.move_right()
                        self.player.move_cooldown = 18
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "pothole":
                    self.slow_timer = max(self.slow_timer, 50)
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)
                elif obs.kind == "slow_zone":
                    self.slow_timer = max(self.slow_timer, 90)
                    if obs in self.obstacles:
                        self.obstacles.remove(obs)

        for p in self.powerups[:]:
            if self.player.rect.colliderect(p.rect):
                self.apply_powerup(p.type)
                if p.type == "nitro":
                    self.score += 35
                elif p.type == "shield":
                    self.score += 50
                if p in self.powerups:
                    self.powerups.remove(p)

        for e in self.road_events[:]:
            if self.player.rect.colliderect(e.rect):
                if e.type == "moving_barrier":
                    crashed = self.handle_crash(e)
                    if not crashed and e in self.road_events:
                        self.road_events.remove(e)
                elif e.type == "speed_bump":
                    self.slow_timer = max(self.slow_timer, 40)
                elif e.type == "nitro_strip":
                    if self.active_powerup is None:
                        self.active_powerup = "nitro"
                        self.powerup_end_time = pygame.time.get_ticks() + 3000

        if self.distance >= FINISH_DISTANCE:
            self.state = STATE_GAME_OVER
            self.game_over = True

        if self.state == STATE_GAME_OVER and not self.leaderboard_saved:
            add_score_to_leaderboard(self.username if self.username.strip() else "Player", self.score, self.distance, self.coins)
            self.leaderboard_saved = True

    def draw_road(self):
        SCREEN.fill(BG)
        pygame.draw.rect(SCREEN, ROAD, (ROAD_MARGIN, 0, ROAD_WIDTH, HEIGHT))
        pygame.draw.rect(SCREEN, WHITE, (ROAD_MARGIN - 4, 0, 4, HEIGHT))
        pygame.draw.rect(SCREEN, WHITE, (ROAD_MARGIN + ROAD_WIDTH, 0, 4, HEIGHT))

        for i in range(1, LANE_COUNT):
            x = ROAD_MARGIN + i * LANE_WIDTH
            for y in range(-40, HEIGHT, 80):
                pygame.draw.rect(SCREEN, ROAD_LINE, (x - 4, y + int(self.road_offset), 8, 40), border_radius=3)

    def draw_hud(self):
        remaining = max(0, int(FINISH_DISTANCE - self.distance))
        pygame.draw.rect(SCREEN, (0, 0, 0), (8, 8, 220, 132), border_radius=12)
        pygame.draw.rect(SCREEN, WHITE, (8, 8, 220, 132), 2, border_radius=12)

        draw_text(f"Player: {self.username if self.username else 'Player'}", FONT_TINY, WHITE, SCREEN, 18, 16)
        draw_text(f"Score: {int(self.score)}", FONT_SMALL, WHITE, SCREEN, 18, 34)
        draw_text(f"Coins: {self.coins}", FONT_SMALL, WHITE, SCREEN, 18, 58)
        draw_text(f"Distance: {int(self.distance)}", FONT_SMALL, WHITE, SCREEN, 18, 82)
        draw_text(f"Remaining: {remaining}", FONT_TINY, WHITE, SCREEN, 18, 108)

        pygame.draw.rect(SCREEN, (0, 0, 0), (250, 8, 222, 132), border_radius=12)
        pygame.draw.rect(SCREEN, WHITE, (250, 8, 222, 132), 2, border_radius=12)

        active_text = "None"
        if self.active_powerup == "nitro":
            remain = max(0, (self.powerup_end_time - pygame.time.get_ticks()) // 1000 + 1)
            active_text = f"Nitro ({remain}s)"
        elif self.shield_active:
            active_text = "Shield"
        elif self.repair_count > 0:
            active_text = f"Repair x{self.repair_count}"

        draw_text("Power-Ups", FONT_SMALL, WHITE, SCREEN, 260, 20)
        draw_text(f"Active: {active_text}", FONT_TINY, WHITE, SCREEN, 260, 50)
        draw_text(f"Shield: {'ON' if self.shield_active else 'OFF'}", FONT_TINY, WHITE, SCREEN, 260, 76)
        draw_text(f"Repair: {self.repair_count}", FONT_TINY, WHITE, SCREEN, 260, 100)

    def draw_main_menu(self):
        SCREEN.fill((25, 25, 35))
        draw_text("RACER GAME", FONT_BIG, WHITE, SCREEN, WIDTH // 2, 120, center=True)
        draw_text("TSIS 3", FONT_MED, YELLOW, SCREEN, WIDTH // 2, 170, center=True)
        for btn in self.menu_buttons:
            btn.draw(SCREEN)

    def draw_username_screen(self):
        SCREEN.fill((25, 25, 35))
        draw_text("Enter Username", FONT_BIG, WHITE, SCREEN, WIDTH // 2, 170, center=True)
        box = pygame.Rect(WIDTH // 2 - 150, 280, 300, 56)
        pygame.draw.rect(SCREEN, WHITE, box, border_radius=10)
        pygame.draw.rect(SCREEN, BLACK, box.inflate(-4, -4), border_radius=10)
        draw_text(self.username if self.username else "Type your name...", FONT_SMALL, WHITE, SCREEN, box.x + 12, box.y + 15)
        draw_text("Press ENTER to start", FONT_SMALL, LIGHT_GRAY, SCREEN, WIDTH // 2, 390, center=True)
        self.back_button.draw(SCREEN)

    def draw_settings(self):
        SCREEN.fill((30, 30, 40))
        draw_text("Settings", FONT_BIG, WHITE, SCREEN, WIDTH // 2, 120, center=True)

        self.sound_button.text = f"Sound: {'On' if self.settings['sound'] else 'Off'}"
        self.color_button.text = f"Car Color: {self.settings['car_color'].title()}"
        self.diff_button.text = f"Difficulty: {self.settings['difficulty'].title()}"

        self.sound_button.draw(SCREEN)
        self.color_button.draw(SCREEN)
        self.diff_button.draw(SCREEN)
        self.settings_back_button.draw(SCREEN)

    def draw_leaderboard(self):
        SCREEN.fill((20, 30, 40))
        draw_text("Top 10 Leaderboard", FONT_MED, WHITE, SCREEN, WIDTH // 2, 60, center=True)
        data = load_leaderboard()

        headers = ["#", "Name", "Score", "Dist"]
        x_positions = [35, 90, 250, 365]
        for i, h in enumerate(headers):
            draw_text(h, FONT_SMALL, YELLOW, SCREEN, x_positions[i], 110)

        y = 150
        if not data:
            draw_text("No scores yet", FONT_MED, LIGHT_GRAY, SCREEN, WIDTH // 2, HEIGHT // 2, center=True)
        else:
            for idx, item in enumerate(data, start=1):
                draw_text(str(idx), FONT_SMALL, WHITE, SCREEN, x_positions[0], y)
                draw_text(item["name"][:10], FONT_SMALL, WHITE, SCREEN, x_positions[1], y)
                draw_text(str(item["score"]), FONT_SMALL, WHITE, SCREEN, x_positions[2], y)
                draw_text(str(item["distance"]), FONT_SMALL, WHITE, SCREEN, x_positions[3], y)
                y += 42

        self.back_button.draw(SCREEN)

    def draw_game_over(self):
        SCREEN.fill((30, 10, 10))
        title = "FINISH!" if self.distance >= FINISH_DISTANCE else "GAME OVER"
        draw_text(title, FONT_BIG, WHITE, SCREEN, WIDTH // 2, 150, center=True)
        draw_text(f"Player: {self.username if self.username else 'Player'}", FONT_MED, YELLOW, SCREEN, WIDTH // 2, 240, center=True)
        draw_text(f"Score: {int(self.score)}", FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 300, center=True)
        draw_text(f"Distance: {int(self.distance)}", FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 340, center=True)
        draw_text(f"Coins: {self.coins}", FONT_SMALL, WHITE, SCREEN, WIDTH // 2, 380, center=True)
        self.retry_button.draw(SCREEN)
        self.main_menu_button.draw(SCREEN)

    def draw_playing(self):
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

    def handle_main_menu_events(self, event):
        if self.menu_buttons[0].clicked(event):
            self.state = STATE_USERNAME
        elif self.menu_buttons[1].clicked(event):
            self.state = STATE_LEADERBOARD
        elif self.menu_buttons[2].clicked(event):
            self.state = STATE_SETTINGS
        elif self.menu_buttons[3].clicked(event):
            self.running = False

    def handle_username_events(self, event):
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if not self.username.strip():
                    self.username = "Player"
                self.start_run()
                self.state = STATE_PLAYING
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            else:
                if len(self.username) < 12 and event.unicode.isprintable():
                    self.username += event.unicode

    def handle_settings_events(self, event):
        if self.sound_button.clicked(event):
            self.settings["sound"] = not self.settings["sound"]
            save_settings(self.settings)

        elif self.color_button.clicked(event):
            colors = list(CAR_COLORS.keys())
            idx = colors.index(self.settings["car_color"])
            self.settings["car_color"] = colors[(idx + 1) % len(colors)]
            save_settings(self.settings)

        elif self.diff_button.clicked(event):
            diffs = list(DIFFICULTY_PRESETS.keys())
            idx = diffs.index(self.settings["difficulty"])
            self.settings["difficulty"] = diffs[(idx + 1) % len(diffs)]
            save_settings(self.settings)

        elif self.settings_back_button.clicked(event):
            self.player.set_color(self.settings["car_color"])
            self.state = STATE_MAIN_MENU

    def handle_leaderboard_events(self, event):
        if self.back_button.clicked(event):
            self.state = STATE_MAIN_MENU

    def handle_game_over_events(self, event):
        if self.retry_button.clicked(event):
            self.start_run()
            self.state = STATE_PLAYING
        elif self.main_menu_button.clicked(event):
            self.state = STATE_MAIN_MENU

    def handle_playing_events(self, event):
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
        if self.state == STATE_PLAYING:
            self.update_playing()

    def draw(self):
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
        pygame.display.flip()

    def run(self):
        while self.running:
            CLOCK.tick(FPS)
            self.events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()