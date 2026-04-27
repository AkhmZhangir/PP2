import psycopg2
from psycopg2 import OperationalError
from config import DB_CONFIG

_conn = None

def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(**DB_CONFIG)
    return _conn

def init_db():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id       SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL
            );
        """)
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
        print(f"[DB] Connection failed: {e}")
        return False

def get_or_create_player(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE username = %s", (username,))
    row = cur.fetchone()
    if row:
        player_id = row[0]
    else:
        cur.execute("INSERT INTO players (username) VALUES (%s) RETURNING id", (username,))
        player_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    return player_id

def save_session(username, score, level_reached):
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
        return [(i+1, r[0], r[1], r[2], r[3]) for i, r in enumerate(rows)]
    except Exception as e:
        print(f"[DB] get_leaderboard error: {e}")
        return []

def get_personal_best(username):
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