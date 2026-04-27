-- 2) Процедура upsert (insert или update по имени)
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_first_name varchar,
    p_last_name  varchar,
    p_phone      varchar,
    p_email      varchar
)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE first_name = p_first_name) THEN
        UPDATE contacts
        SET last_name = p_last_name,
            phone     = p_phone,
            email     = p_email
        WHERE first_name = p_first_name;
    ELSE
        INSERT INTO contacts(first_name, last_name, phone, email)
        VALUES (p_first_name, p_last_name, p_phone, p_email);
    END IF;
END;
$$;

-- Простая проверка телефона: начинаетcя с +7 и 11 цифр всего
CREATE OR REPLACE FUNCTION is_valid_phone(p_phone varchar)
RETURNS boolean AS $$
BEGIN
    RETURN p_phone ~ '^\+7[0-9]{10}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 3) Процедура массовой вставки с валидацией, возвращает неверные записи
CREATE OR REPLACE PROCEDURE bulk_upsert_contacts(
    IN  p_names   varchar[],
    IN  p_phones  varchar[],
    OUT bad_names varchar[],
    OUT bad_phones varchar[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i integer;
BEGIN
    bad_names  := ARRAY[]::varchar[];
    bad_phones := ARRAY[]::varchar[];

    FOR i IN 1 .. array_length(p_names, 1) LOOP
        IF NOT is_valid_phone(p_phones[i]) THEN
            bad_names  := bad_names  || p_names[i];
            bad_phones := bad_phones || p_phones[i];
        ELSE
            CALL upsert_contact(p_names[i], NULL, p_phones[i], NULL);
        END IF;
    END LOOP;
END;
$$;

-- 5) Процедура удаления по имени или телефону
CREATE OR REPLACE PROCEDURE delete_contact_by_name_or_phone(
    p_name  varchar,
    p_phone varchar
)
LANGUAGE plpgsql AS $$
BEGIN
    IF p_name IS NOT NULL THEN
        DELETE FROM contacts WHERE first_name = p_name;
    END IF;

    IF p_phone IS NOT NULL THEN
        DELETE FROM contacts WHERE phone = p_phone;
    END IF;
END;
$$;

-- Новые объекты для TSIS1

-- Процедура add_phone: добавить новый телефон к существующему контакту
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type: %', p_type;
    END IF;

    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name = p_contact_name
    ORDER BY id
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact with name % not found', p_contact_name;
    END IF;

    INSERT INTO phones(contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);
END;
$$;

-- Процедура move_to_group: переместить контакт в другую группу (создаёт группу при необходимости)
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_group_id   INTEGER;
    v_contact_id INTEGER;
BEGIN
    IF p_group_name IS NULL OR trim(p_group_name) = '' THEN
        RAISE EXCEPTION 'Group name must not be empty';
    END IF;

    SELECT id INTO v_group_id
    FROM groups
    WHERE name = p_group_name;

    IF v_group_id IS NULL THEN
        INSERT INTO groups(name) VALUES (p_group_name) RETURNING id INTO v_group_id;
    END IF;

    SELECT id INTO v_contact_id
    FROM contacts
    WHERE first_name = p_contact_name
    ORDER BY id
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact with name % not found', p_contact_name;
    END IF;

    UPDATE contacts
    SET group_id = v_group_id
    WHERE id = v_contact_id;
END;
$$;

-- Функция search_contacts: ищет по имени, фамилии, email и всем телефонам
CREATE OR REPLACE FUNCTION search_contacts(
    p_query TEXT
)
RETURNS TABLE (
    id         INTEGER,
    first_name VARCHAR,
    last_name  VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phone      VARCHAR,
    phone_type VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
           c.id,
           c.first_name,
           c.last_name,
           c.email,
           c.birthday,
           g.name AS group_name,
           p.phone,
           p.type
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE p_query IS NULL
       OR p_query = ''
       OR c.first_name ILIKE '%' || p_query || '%'
       OR c.last_name  ILIKE '%' || p_query || '%'
       OR c.email      ILIKE '%' || p_query || '%'
       OR p.phone      ILIKE '%' || p_query || '%';
END;
$$;