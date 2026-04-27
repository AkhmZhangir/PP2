# main.py — Точка входа в приложение Snake Game (TSIS 4)
# Управляет экранами, событиями, состоянием игры и интеграцией с БД

import pygame, sys, random
from config import *                          # Константы: WIDTH, HEIGHT, цвета, FPS и т.д.
from game import SnakeGame, _t               # Логика игры и вспомогательная функция отрисовки текста
from db import init_db, save_session, get_leaderboard, get_personal_best  # Функции работы с PostgreSQL
from settings_manager import load_settings, save_settings  # Чтение/запись settings.json

# Инициализация Pygame и создание главного окна
pygame.init()
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSIS 4 — Snake Game")
CLOCK = pygame.time.Clock()  # Контролирует частоту кадров (60 FPS)

# Шрифты разных размеров для заголовков, меню, HUD и мелкого текста
FONT_TITLE = pygame.font.SysFont("arial", 44, bold=True)
FONT_BIG   = pygame.font.SysFont("arial", 32, bold=True)
FONT_MED   = pygame.font.SysFont("arial", 24, bold=True)
FONT_SMALL = pygame.font.SysFont("arial", 18)
FONT_TINY  = pygame.font.SysFont("arial", 15)

# Константы состояний — определяют текущий активный экран
S_MENU       = "MENU"
S_USERNAME   = "USERNAME"
S_PLAYING    = "PLAYING"
S_GAME_OVER  = "GAME_OVER"
S_LEADERBOARD= "LEADERBOARD"
S_SETTINGS   = "SETTINGS"

# Инициализация БД при старте; DB_OK=False если PostgreSQL недоступен
DB_OK = init_db()


class Button:
    """Кнопка с эффектом наведения (hover) и скруглёнными углами."""

    def __init__(self, x, y, w, h, text, bg=(80,80,80), hover=(130,130,130), fg=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.bg, self.hover, self.fg = text, bg, hover, fg

    def draw(self, surf):
        """Рисует кнопку: меняет цвет при наведении мыши."""
        mx, my = pygame.mouse.get_pos()
        col = self.hover if self.rect.collidepoint(mx, my) else self.bg
        pygame.draw.rect(surf, col, self.rect, border_radius=12)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=12)  # Белая рамка
        img = FONT_SMALL.render(self.text, True, self.fg)
        surf.blit(img, img.get_rect(center=self.rect.center))

    def clicked(self, event):
        """Возвращает True, если произошёл клик левой кнопкой мыши по кнопке."""
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


class App:
    """Главный класс приложения — управляет конечным автоматом экранов (FSM)."""

    def __init__(self):
        self.state = S_MENU              # Начальный экран — главное меню
        self.settings = load_settings() # Загружаем настройки из settings.json
        self.username = ""              # Имя игрока, введённое на экране USERNAME
        self.typing = ""               # Буфер ввода текста для поля имени
        self.snake_game = None         # Экземпляр SnakeGame (создаётся при старте игры)
        self.personal_best = 0         # Лучший счёт текущего игрока из БД
        self.last_score = 0            # Счёт последней завершённой партии
        self.last_level = 1            # Уровень, достигнутый в последней партии
        self.last_reason = ""          # Причина окончания игры (столкновение, яд и т.д.)
        self.session_saved = False     # Флаг: результат уже сохранён в БД (избегаем дублей)
        self.snake_timer = 0           # Накопленное время для пошагового движения змейки (мс)
        self._build_buttons()

    def _build_buttons(self):
        """Создаёт все кнопки интерфейса и список вариантов цвета змейки."""
        cx = WIDTH // 2

        # Кнопки главного меню
        self.btn_play  = Button(cx-110, 290, 220, 55, "Play")
        self.btn_lb    = Button(cx-110, 360, 220, 55, "Leaderboard")
        self.btn_set   = Button(cx-110, 430, 220, 55, "Settings")
        self.btn_quit  = Button(cx-110, 500, 220, 55, "Quit")

        # Универсальная кнопка «Назад» (левый верхний угол)
        self.btn_back  = Button(20, 20, 110, 44, "Back")

        # Кнопки экрана Game Over
        self.btn_retry = Button(cx-110, 440, 220, 55, "Retry")
        self.btn_menu  = Button(cx-110, 510, 220, 55, "Main Menu")

        # Кнопки экрана настроек (текст обновляется динамически)
        self.btn_grid  = Button(cx-110, 240, 220, 48, "")
        self.btn_sound = Button(cx-110, 310, 220, 48, "")
        self.btn_color = Button(cx-110, 380, 220, 48, "")
        self.btn_save  = Button(cx-110, 470, 220, 52, "Save & Back")

        # Доступные цвета змейки и их названия
        self._color_opts  = [[80,200,80],[80,140,255],[240,200,60],[220,80,80],[200,100,255]]
        self._color_names = ["Green","Blue","Yellow","Red","Purple"]
        self._color_idx = 0

        # Устанавливаем индекс цвета в соответствии с сохранёнными настройками
        for i, c in enumerate(self._color_opts):
            if c == self.settings["snake_color"]:
                self._color_idx = i
                break

    # ──────────────────────────────────────────────
    # Главный игровой цикл
    # ──────────────────────────────────────────────

    def run(self):
        """Главный цикл: обрабатывает события → обновляет логику → рисует кадр."""
        while True:
            dt = CLOCK.tick(60)  # dt — миллисекунды с прошлого кадра (max 60 FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                # Маршрутизация событий в зависимости от текущего экрана
                if   self.state == S_MENU:        self._ev_menu(event)
                elif self.state == S_USERNAME:    self._ev_username(event)
                elif self.state == S_PLAYING:     self._ev_playing(event)
                elif self.state == S_GAME_OVER:   self._ev_gameover(event)
                elif self.state == S_LEADERBOARD:
                    if self.btn_back.clicked(event): self.state = S_MENU
                elif self.state == S_SETTINGS:    self._ev_settings(event)

            self._update(dt)  # Обновление игровой логики
            self._draw()      # Отрисовка текущего экрана

    # ──────────────────────────────────────────────
    # Обработчики событий по экранам
    # ──────────────────────────────────────────────

    def _ev_menu(self, ev):
        """Обработка кликов на главном меню."""
        if   self.btn_play.clicked(ev):  self.state = S_USERNAME; self.typing = self.username
        elif self.btn_lb.clicked(ev):    self.state = S_LEADERBOARD
        elif self.btn_set.clicked(ev):   self.state = S_SETTINGS
        elif self.btn_quit.clicked(ev):  pygame.quit(); sys.exit()

    def _ev_username(self, ev):
        """Обработка ввода имени: печать символов, Backspace, Enter для старта."""
        if self.btn_back.clicked(ev): self.state = S_MENU
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                # Подтверждение имени; «Player» по умолчанию если поле пустое
                self.username = self.typing.strip() or "Player"
                self._start_game()
            elif ev.key == pygame.K_BACKSPACE:
                self.typing = self.typing[:-1]          # Удаляем последний символ
            elif ev.unicode.isprintable() and len(self.typing) < 16:
                self.typing += ev.unicode               # Добавляем символ (макс. 16)

    def _ev_playing(self, ev):
        """Обработка управления змейкой: стрелки и WASD; ESC — выход в меню."""
        if ev.type == pygame.KEYDOWN:
            k = ev.key
            if k == pygame.K_ESCAPE:                      self.state = S_MENU
            elif k in (pygame.K_UP,    pygame.K_w):       self.snake_game.change_direction("UP")
            elif k in (pygame.K_DOWN,  pygame.K_s):       self.snake_game.change_direction("DOWN")
            elif k in (pygame.K_LEFT,  pygame.K_a):       self.snake_game.change_direction("LEFT")
            elif k in (pygame.K_RIGHT, pygame.K_d):       self.snake_game.change_direction("RIGHT")

    def _ev_gameover(self, ev):
        """Обработка кнопок на экране Game Over."""
        if   self.btn_retry.clicked(ev): self._start_game()       # Новая партия с тем же именем
        elif self.btn_menu.clicked(ev):  self.state = S_MENU

    def _ev_settings(self, ev):
        """Переключение настроек; сохранение происходит только по кнопке Save & Back."""
        if   self.btn_grid.clicked(ev):
            self.settings["grid_overlay"] = not self.settings["grid_overlay"]  # Вкл/выкл сетку
        elif self.btn_sound.clicked(ev):
            self.settings["sound"] = not self.settings["sound"]                # Вкл/выкл звук
        elif self.btn_color.clicked(ev):
            # Циклический перебор доступных цветов змейки
            self._color_idx = (self._color_idx + 1) % len(self._color_opts)
            self.settings["snake_color"] = self._color_opts[self._color_idx]
        elif self.btn_save.clicked(ev):
            save_settings(self.settings)   # Записываем настройки в settings.json
            self.state = S_MENU
        elif self.btn_back.clicked(ev):
            self.state = S_MENU            # Выход без сохранения

    # ──────────────────────────────────────────────
    # Инициализация и обновление игры
    # ──────────────────────────────────────────────

    def _start_game(self):
        """Создаёт новый экземпляр SnakeGame и загружает личный рекорд игрока из БД."""
        self.personal_best = get_personal_best(self.username) if DB_OK else 0
        self.settings = load_settings()  # Перечитываем настройки на случай изменений
        self.snake_game = SnakeGame(self.settings, self.username, self.personal_best)
        self.snake_timer = 0
        self.session_saved = False
        self.state = S_PLAYING

    def _update(self, dt):
        """
        Обновляет игровую логику с фиксированным шагом, зависящим от текущего FPS змейки.
        Использует накопленный таймер чтобы отвязать скорость змейки от FPS рендера.
        После game over — сохраняет результат в БД ровно один раз.
        """
        if self.state != S_PLAYING or not self.snake_game:
            return

        step_ms = 1000 // self.snake_game.current_fps  # Интервал одного шага в мс
        self.snake_timer += dt

        # Выполняем столько шагов, сколько накопилось времени
        while self.snake_timer >= step_ms:
            self.snake_timer -= step_ms
            self.snake_game.update()

        # Если игра завершилась — сохраняем сессию в БД (флаг предотвращает повтор)
        if self.snake_game.game_over and not self.session_saved:
            self.last_score  = self.snake_game.score
            self.last_level  = self.snake_game.level
            self.last_reason = self.snake_game.game_over_reason
            if DB_OK:
                save_session(self.username, self.last_score, self.last_level)
            # Обновляем личный рекорд после сохранения
            self.personal_best = get_personal_best(self.username) if DB_OK else self.last_score
            self.session_saved = True
            self.state = S_GAME_OVER

    # ──────────────────────────────────────────────
    # Отрисовка экранов
    # ──────────────────────────────────────────────

    def _draw(self):
        """Очищает экран и вызывает нужный метод отрисовки в зависимости от состояния."""
        SCREEN.fill(BG)
        if   self.state == S_MENU:          self._draw_menu()
        elif self.state == S_USERNAME:      self._draw_username()
        elif self.state == S_PLAYING:       self._draw_playing()
        elif self.state == S_GAME_OVER:     self._draw_gameover()
        elif self.state == S_LEADERBOARD:   self._draw_leaderboard()
        elif self.state == S_SETTINGS:      self._draw_settings()
        pygame.display.flip()  # Отображаем готовый кадр

    def _draw_menu(self):
        """Главное меню: заголовок, подзаголовок, предупреждение об офлайн-режиме БД."""
        cx = WIDTH // 2
        _t(FONT_TITLE, "SNAKE GAME", WHITE, SCREEN, cx, 100, center=True)
        _t(FONT_SMALL, "TSIS 4", (160,160,160), SCREEN, cx, 160, center=True)
        if not DB_OK:
            # Оповещаем игрока, что результаты не будут сохранены
            _t(FONT_TINY, "DB offline — scores won't be saved", (200,80,80), SCREEN, cx, 210, center=True)
        self.btn_play.draw(SCREEN); self.btn_lb.draw(SCREEN)
        self.btn_set.draw(SCREEN);  self.btn_quit.draw(SCREEN)

    def _draw_username(self):
        """Экран ввода имени: текстовое поле с курсором-плейсхолдером."""
        cx = WIDTH // 2
        _t(FONT_BIG, "Enter Username", WHITE, SCREEN, cx, 180, center=True)

        # Рамка поля ввода: белый контур + чёрный фон
        box = pygame.Rect(cx-160, 280, 320, 56)
        pygame.draw.rect(SCREEN, WHITE, box, border_radius=10)
        pygame.draw.rect(SCREEN, BLACK, box.inflate(-4, -4), border_radius=10)

        # Показываем введённый текст или серый плейсхолдер
        _t(FONT_SMALL, self.typing or "Type your name...",
           WHITE if self.typing else GRAY, SCREEN, box.x+12, box.y+15)
        _t(FONT_SMALL, "Press ENTER to start", LIGHT_GRAY, SCREEN, cx, 380, center=True)
        self.btn_back.draw(SCREEN)

    def _draw_playing(self):
        """Делегирует отрисовку поля и HUD объекту SnakeGame."""
        if self.snake_game:
            self.snake_game.draw(SCREEN)                           # Поле, еда, препятствия
            self.snake_game.draw_hud(SCREEN, FONT_MED, FONT_SMALL) # Счёт, уровень, рекорд

    def _draw_gameover(self):
        """Экран Game Over: причина, счёт, уровень, личный рекорд, кнопки."""
        cx = WIDTH // 2
        _t(FONT_TITLE, "GAME OVER", (220,60,60), SCREEN, cx, 130, center=True)
        _t(FONT_SMALL, self.last_reason, LIGHT_GRAY, SCREEN, cx, 195, center=True)
        _t(FONT_MED,   f"Score: {self.last_score}", WHITE, SCREEN, cx, 240, center=True)
        _t(FONT_SMALL, f"Level reached: {self.last_level}", LIGHT_GRAY, SCREEN, cx, 290, center=True)
        _t(FONT_SMALL, f"Personal best: {self.personal_best}", YELLOW, SCREEN, cx, 325, center=True)
        self.btn_retry.draw(SCREEN); self.btn_menu.draw(SCREEN)

    def _draw_leaderboard(self):
        """
        Таблица Top-10: загружает данные из PostgreSQL и отрисовывает строки с рангом,
        именем, счётом, уровнем и датой. При офлайн-режиме БД — показывает сообщение.
        """
        cx = WIDTH // 2
        _t(FONT_BIG, "Top 10 Leaderboard", WHITE, SCREEN, cx, 60, center=True)

        if not DB_OK:
            _t(FONT_SMALL, "Database is offline", (200,80,80), SCREEN, cx, HEIGHT//2, center=True)
            self.btn_back.draw(SCREEN)
            return

        data = get_leaderboard(10)  # Запрос TOP-10 из таблицы game_sessions

        # Позиции колонок по X
        xs = [28, 70, 270, 360, 430]
        for h, c in zip(["#", "Name", "Score", "Lvl", "Date"], [YELLOW]*5):
            _t(FONT_SMALL, h, c, SCREEN, xs[0 + ["#","Name","Score","Lvl","Date"].index(h)], 120)

        y = 158  # Начальная Y-позиция первой строки данных
        if not data:
            _t(FONT_SMALL, "No scores yet!", LIGHT_GRAY, SCREEN, cx, 300, center=True)
        else:
            for rank, uname, score, level, played_at in data:
                ds = played_at.strftime("%m/%d %H:%M") if played_at else "-"
                _t(FONT_SMALL, str(rank),      WHITE,      SCREEN, xs[0], y)
                _t(FONT_SMALL, uname[:14],     WHITE,      SCREEN, xs[1], y)  # Обрезаем длинные имена
                _t(FONT_SMALL, str(score),     WHITE,      SCREEN, xs[2], y)
                _t(FONT_SMALL, str(level),     LIGHT_GRAY, SCREEN, xs[3], y)
                _t(FONT_TINY,  ds,             LIGHT_GRAY, SCREEN, xs[4], y+2)
                y += 44  # Шаг между строками таблицы
        self.btn_back.draw(SCREEN)

    def _draw_settings(self):
        """
        Экран настроек: кнопки-переключатели для сетки, звука и цвета змейки.
        Цветной прямоугольник-превью показывает выбранный цвет змейки.
        """
        cx = WIDTH // 2
        _t(FONT_BIG, "Settings", WHITE, SCREEN, cx, 120, center=True)

        # Обновляем текст кнопок в соответствии с текущими значениями настроек
        self.btn_grid.text  = f"Grid: {'On' if self.settings['grid_overlay'] else 'Off'}"
        self.btn_sound.text = f"Sound: {'On' if self.settings['sound'] else 'Off'}"
        self.btn_color.text = f"Color: {self._color_names[self._color_idx]}"

        # Фон кнопки цвета = приглушённый вариант выбранного цвета змейки
        sc = self.settings["snake_color"]
        self.btn_color.bg = tuple(max(c-60, 20) for c in sc)

        self.btn_grid.draw(SCREEN)
        self.btn_sound.draw(SCREEN)
        self.btn_color.draw(SCREEN)

        # Маленький цветной квадрат-превью рядом с кнопкой выбора цвета
        prev = pygame.Rect(cx-20, 445, 40, 40)
        pygame.draw.rect(SCREEN, tuple(sc), prev, border_radius=8)
        pygame.draw.rect(SCREEN, WHITE, prev, 2, border_radius=8)

        self.btn_save.draw(SCREEN)


# Точка входа: создаём приложение и запускаем главный цикл
if __name__ == "__main__":
    app = App()
    app.run()