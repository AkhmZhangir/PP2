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

