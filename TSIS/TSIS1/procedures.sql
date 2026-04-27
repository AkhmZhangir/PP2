-- procedures.sql — полный набор
-- Запуск: psql -d phonebook -f procedures.sql

-- ════════════════════════════════════════════════════════
--  TSIS — базовые процедуры
-- ════════════════════════════════════════════════════════

-- Upsert: добавить или обновить контакт по телефону
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name VARCHAR,
    p_last_name  VARCHAR,
    p_phone      VARCHAR,
    p_email      VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO contacts (first_name, last_name, phone, email)
    VALUES (p_first_name, p_last_name, p_phone, p_email)
    ON CONFLICT (phone) DO UPDATE
        SET first_name = EXCLUDED.first_name,
            last_name  = EXCLUDED.last_name,
            email      = EXCLUDED.email;
END;
$$;

-- Удаление по имени или телефону
CREATE OR REPLACE PROCEDURE delete_contact_by_name_or_phone(
    p_name  VARCHAR,
    p_phone VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_name IS NOT NULL THEN
        DELETE FROM contacts WHERE first_name = p_name;
    ELSIF p_phone IS NOT NULL THEN
        DELETE FROM contacts WHERE phone = p_phone;
    END IF;
END;
$$;

-- Массовое добавление контактов
CREATE OR REPLACE PROCEDURE bulk_upsert_contacts(
    p_names  VARCHAR[],
    p_phones VARCHAR[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i INTEGER;
BEGIN
    FOR i IN 1..array_length(p_names, 1) LOOP
        INSERT INTO contacts (first_name, phone)
        VALUES (p_names[i], p_phones[i])
        ON CONFLICT (phone) DO UPDATE
            SET first_name = EXCLUDED.first_name;
    END LOOP;
END;
$$;

-- Поиск по шаблону (имя / фамилия / телефон)
CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p_pattern VARCHAR)
RETURNS TABLE (
    contact_id INTEGER,
    first_name VARCHAR,
    last_name  VARCHAR,
    phone      VARCHAR,
    email      VARCHAR
)
LANGUAGE sql AS $$
    SELECT contact_id, first_name, last_name, phone, email
    FROM contacts
    WHERE first_name ILIKE '%' || p_pattern || '%'
       OR last_name  ILIKE '%' || p_pattern || '%'
       OR phone      ILIKE '%' || p_pattern || '%'
    ORDER BY first_name;
$$;

-- Пагинация
CREATE OR REPLACE FUNCTION get_contacts_page(p_limit INTEGER, p_offset INTEGER)
RETURNS TABLE (
    contact_id INTEGER,
    first_name VARCHAR,
    last_name  VARCHAR,
    phone      VARCHAR,
    email      VARCHAR,
    birthday   DATE
)
LANGUAGE sql AS $$
    SELECT contact_id, first_name, last_name, phone, email, birthday
    FROM contacts
    ORDER BY contact_id
    LIMIT p_limit OFFSET p_offset;
$$;


-- Добавить доп. телефон контакту
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INTEGER;
BEGIN
    SELECT contact_id INTO v_id
    FROM contacts WHERE first_name = p_contact_name LIMIT 1;

    IF v_id IS NULL THEN
        RAISE EXCEPTION 'Контакт "%" не найден', p_contact_name;
    END IF;

    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Недопустимый тип телефона: %. Допустимо: home, work, mobile', p_type;
    END IF;

    INSERT INTO phones (contact_id, phone, type) VALUES (v_id, p_phone, p_type);
END;
$$;

-- Переместить контакт в группу (создаёт группу при отсутствии)
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    SELECT contact_id INTO v_contact_id
    FROM contacts WHERE first_name = p_contact_name LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Контакт "%" не найден', p_contact_name;
    END IF;

    INSERT INTO groups (name) VALUES (p_group_name) ON CONFLICT (name) DO NOTHING;
    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    UPDATE contacts SET group_id = v_group_id WHERE contact_id = v_contact_id;
END;
$$;

-- Расширенный поиск: имя + фамилия + email + все телефоны
CREATE OR REPLACE FUNCTION search_contacts(p_query VARCHAR)
RETURNS TABLE (
    contact_id INTEGER,
    first_name VARCHAR,
    last_name  VARCHAR,
    phone      VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.contact_id,
        c.first_name,
        c.last_name,
        c.phone,
        c.email,
        c.birthday,
        g.name AS group_name
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.contact_id
    WHERE
        c.first_name ILIKE '%' || p_query || '%'
     OR c.last_name  ILIKE '%' || p_query || '%'
     OR c.phone      ILIKE '%' || p_query || '%'
     OR c.email      ILIKE '%' || p_query || '%'
     OR p.phone      ILIKE '%' || p_query || '%';
END;
$$;