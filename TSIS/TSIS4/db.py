# db.py — Работа с PostgreSQL через psycopg2: инициализация БД, сохранение сессий, лидерборд

import psycopg2
from psycopg2 import OperationalError
from config import DB_CONFIG  # Словарь с параметрами подключения: host, port, dbname, user, password

# Глобальное соединение — переиспользуется во всех функциях (паттерн «singleton connection»)
_conn = None


def get_conn():
    """
    Возвращает активное соединение с БД.
    Если соединение отсутствует или закрыто — создаёт новое.
    Используется всеми функциями модуля вместо прямого вызова psycopg2.connect().
    """
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(**DB_CONFIG)
    return _conn


def init_db():
    """
    Создаёт таблицы players и game_sessions при первом запуске (если они не существуют).

    Схема:
      players       — уникальные игроки (id, username)
      game_sessions — каждая сыгранная партия (ссылка на player_id, счёт, уровень, время)

    Возвращает True при успехе, False если PostgreSQL недоступен.
    При ошибке подключения игра продолжает работать в офлайн-режиме (DB_OK = False).
    """
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Таблица игроков: username уникален — один игрок не дублируется
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id       SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL
            );
        """)

        # Таблица сессий: каждая запись — одна завершённая партия
        # played_at заполняется автоматически текущим временем сервера
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                id            SERIAL PRIMARY KEY,
                player_id     INTEGER REFERENCES players(id),
                score         INTEGER   NOT NULL,
                level_reached INTEGER   NOT NULL,
                played_at     TIMESTAMP DEFAULT NOW()
            );
        """)

        conn.commit()
        cur.close()
        return True

    except OperationalError as e:
        # Соединение не установлено — PostgreSQL не запущен или неверный DB_CONFIG
        print(f"[DB] Connection failed: {e}")
        return False


def get_or_create_player(username):
    """
    Возвращает id игрока по имени.
    Если игрок ещё не существует в таблице players — создаёт его и возвращает новый id.
    Гарантирует, что одно имя = одна строка в players (за счёт UNIQUE NOT NULL).
    """
    conn = get_conn()
    cur = conn.cursor()

    # Проверяем, есть ли уже такой игрок
    cur.execute("SELECT id FROM players WHERE username = %s", (username,))
    row = cur.fetchone()

    if row:
        player_id = row[0]           # Игрок найден — берём существующий id
    else:
        # Новый игрок — вставляем и сразу возвращаем присвоенный id через RETURNING
        cur.execute("INSERT INTO players (username) VALUES (%s) RETURNING id", (username,))
        player_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    return player_id


def save_session(username, score, level_reached):
    """
    Сохраняет результат партии в game_sessions.
    Вызывается из App._update() ровно один раз после game_over (флаг session_saved).

    Шаги:
      1. Получает (или создаёт) player_id по имени игрока.
      2. Вставляет строку с очками и достигнутым уровнем.
      3. played_at проставляется PostgreSQL автоматически (DEFAULT NOW()).
    """
    try:
        pid = get_or_create_player(username)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO game_sessions (player_id, score, level_reached)
            VALUES (%s, %s, %s)
        """, (pid, score, level_reached))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[DB] save_session error: {e}")


def get_leaderboard(limit=10):
    """
    Возвращает Top-N всех игроков по убыванию очков.
    При равном счёте более свежие результаты идут выше (ORDER BY played_at DESC).

    Возвращает список кортежей:
      (rank, username, score, level_reached, played_at)

    rank — порядковый номер, добавляется в Python через enumerate (не SQL ROW_NUMBER).
    При ошибке возвращает пустой список — экран лидерборда покажет «No scores yet!».
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.username, gs.score, gs.level_reached, gs.played_at
            FROM game_sessions gs
            JOIN players p ON gs.player_id = p.id
            ORDER BY gs.score DESC, gs.played_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        # Добавляем ранг начиная с 1 через enumerate
        return [(i+1, r[0], r[1], r[2], r[3]) for i, r in enumerate(rows)]
    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []


def get_personal_best(username):
    """
    Возвращает максимальный счёт конкретного игрока по всем его сессиям.
    Используется в двух местах:
      - при старте игры (_start_game) — для отображения Best в HUD
      - после game over (_update) — для обновления рекорда на экране Game Over

    Возвращает 0 если у игрока нет ни одной записи или при ошибке БД.
    MAX(gs.score) вернёт NULL для нового игрока — обрабатываем через «or 0».
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(gs.score)
            FROM game_sessions gs
            JOIN players p ON gs.player_id = p.id
            WHERE p.username = %s
        """, (username,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row and row[0] is not None else 0
    except Exception as e:
        print(f"[DB] get_personal_best error: {e}")
        return 0