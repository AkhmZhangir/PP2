-- schema.sql — полная схема базы данных (Practice 9)
-- Запускать один раз: psql -d phonebook -f schema.sql

-- ─── Таблица групп (Family / Work / Friend / Other) ──────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Предзаполняем стандартные группы
INSERT INTO groups (name) VALUES
    ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;

-- ─── Основная таблица контактов ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    id         SERIAL PRIMARY KEY,
    first_name VARCHAR(50)  NOT NULL,
    last_name  VARCHAR(50),
    phone      VARCHAR(20)  UNIQUE NOT NULL,   -- основной телефон (из Practice 7-8)
    email      VARCHAR(100),                   -- добавлено в Practice 9
    birthday   DATE,                           -- добавлено в Practice 9
    group_id   INTEGER REFERENCES groups(id),  -- добавлено в Practice 9
    created_at TIMESTAMP DEFAULT NOW()
);

-- Добавляем новые колонки, если таблица уже существует (безопасный ALTER)
ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS email     VARCHAR(100),
    ADD COLUMN IF NOT EXISTS birthday  DATE,
    ADD COLUMN IF NOT EXISTS group_id  INTEGER REFERENCES groups(id);

-- ─── Таблица телефонов (1 контакт → много телефонов) ─────────────────────────
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER      NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20)  NOT NULL,
    type       VARCHAR(10)  CHECK (type IN ('home', 'work', 'mobile'))
);