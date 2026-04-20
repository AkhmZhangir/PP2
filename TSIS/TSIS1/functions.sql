CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p_pattern text)
RETURNS TABLE(
    contact_id  integer,
    first_name  varchar,
    last_name   varchar,
    phone       varchar,
    email       varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.contact_id, c.first_name, c.last_name, c.phone, c.email
    FROM contacts c
    WHERE c.first_name ILIKE '%' || p_pattern || '%'
       OR c.last_name  ILIKE '%' || p_pattern || '%'
       OR c.phone      ILIKE '%' || p_pattern || '%';
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_contacts_page(p_limit integer, p_offset integer)
RETURNS TABLE(
    contact_id  integer,
    first_name  varchar,
    last_name   varchar,
    phone       varchar,
    email       varchar
) AS $$
BEGIN
    RETURN QUERY
    SELECT contact_id, first_name, last_name, phone, email
    FROM contacts
    ORDER BY contact_id
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;