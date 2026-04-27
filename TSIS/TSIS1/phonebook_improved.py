"""
Улучшенная версия phonebook.py для TSIS 1.

Что добавлено относительно исходного файла:
- подготовка к расширенной модели контактов;
- поиск по email;
- фильтр по группе;
- сортировка по имени / дате рождения / дате добавления;
- консольная пагинация next / prev / quit поверх существующей DB-функции;
- экспорт в JSON;
- импорт из JSON с обработкой дублей по имени (skip / overwrite);
- расширенный CSV-импорт для новых полей;
- вызов новых процедур add_phone и move_to_group;
- вызов новой функции search_contacts.
"""

import csv
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

PHONE_TYPES = {"home", "work", "mobile"}
SORT_FIELDS = {
    "name": "c.first_name, c.last_name",
    "birthday": "c.birthday NULLS LAST, c.first_name",
    "date": "c.created_at DESC NULLS LAST, c.first_name"
}


def get_connection():
    """Создаёт подключение к PostgreSQL по параметрам из config.py."""
    return psycopg2.connect(**config())


def parse_date(value):
    """Преобразует строку YYYY-MM-DD в date, пустое значение -> None."""
    if not value:
        return None
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def get_or_create_group(cur, group_name):
    """Возвращает id группы; если группы нет, создаёт её."""
    if not group_name:
        return None
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO groups(name) VALUES (%s) RETURNING id", (group_name,))
    return cur.fetchone()[0]


def get_contact_id_by_name(cur, first_name, last_name=None):
    """Ищет контакт по имени и фамилии. Возвращает id или None."""
    if last_name:
        cur.execute(
            "SELECT id FROM contacts WHERE first_name = %s AND last_name = %s",
            (first_name, last_name)
        )
    else:
        cur.execute(
            "SELECT id FROM contacts WHERE first_name = %s ORDER BY id LIMIT 1",
            (first_name,)
        )
    row = cur.fetchone()
    return row[0] if row else None


def upsert_extended_contact(cur, first_name, last_name, email, birthday, group_name,
                            phone, phone_type, overwrite=False):
    """Добавляет или обновляет расширенный контакт и его телефон."""
    group_id = get_or_create_group(cur, group_name)
    contact_id = get_contact_id_by_name(cur, first_name, last_name)

    if contact_id and not overwrite:
        return "duplicate"

    if contact_id and overwrite:
        cur.execute(
            """
            UPDATE contacts
            SET last_name = %s,
                email = %s,
                birthday = %s,
                group_id = %s
            WHERE id = %s
            """,
            (last_name, email, birthday, group_id, contact_id)
        )
        if phone:
            cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))
            cur.execute(
                "INSERT INTO phones(contact_id, phone, type) VALUES (%s, %s, %s)",
                (contact_id, phone, phone_type)
            )
        return "updated"

    cur.execute(
        """
        INSERT INTO contacts(first_name, last_name, email, birthday, group_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (first_name, last_name, email, birthday, group_id)
    )
    contact_id = cur.fetchone()[0]

    if phone:
        cur.execute(
            "INSERT INTO phones(contact_id, phone, type) VALUES (%s, %s, %s)",
            (contact_id, phone, phone_type)
        )
    return "inserted"


def import_from_csv(filename='contacts.csv'):
    """Расширенный импорт CSV: first_name,last_name,email,birthday,group,phone,phone_type."""
    inserted = updated = skipped = 0
    with get_connection() as conn, conn.cursor() as cur, open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            phone_type = (row.get('phone_type') or 'mobile').strip().lower()
            if phone_type not in PHONE_TYPES:
                print(f"Пропуск строки: неверный тип телефона -> {phone_type}")
                skipped += 1
                continue
            result = upsert_extended_contact(
                cur,
                row.get('first_name'),
                row.get('last_name') or None,
                row.get('email') or None,
                parse_date(row.get('birthday')),
                row.get('group') or 'Other',
                row.get('phone') or None,
                phone_type,
                overwrite=True
            )
            if result == 'inserted':
                inserted += 1
            elif result == 'updated':
                updated += 1
    print(f"CSV импорт завершён: inserted={inserted}, updated={updated}, skipped={skipped}")


def insert_from_console():
    """Добавляет расширенный контакт из консоли."""
    first_name = input("Имя: ").strip()
    last_name = input("Фамилия (можно пусто): ").strip() or None
    email = input("Email (можно пусто): ").strip() or None
    birthday = parse_date(input("Дата рождения YYYY-MM-DD (можно пусто): ").strip() or None)
    group_name = input("Группа (Family/Work/Friend/Other): ").strip() or 'Other'
    phone = input("Телефон: ").strip() or None
    phone_type = input("Тип телефона (home/work/mobile): ").strip().lower() or 'mobile'

    if phone_type not in PHONE_TYPES:
        print("Неверный тип телефона")
        return

    with get_connection() as conn, conn.cursor() as cur:
        result = upsert_extended_contact(
            cur, first_name, last_name, email, birthday, group_name, phone, phone_type, overwrite=False
        )
    print("Контакт добавлен" if result == 'inserted' else "Контакт с таким именем уже существует")


def query_contacts():
    """Фильтр по группе, поиск по email, сортировка."""
    group_name = input("Фильтр по группе (Enter чтобы пропустить): ").strip() or None
    email_part = input("Поиск по email (Enter чтобы пропустить): ").strip() or None
    sort_key = input("Сортировка (name/birthday/date): ").strip().lower() or 'name'
    order_by = SORT_FIELDS.get(sort_key, SORT_FIELDS['name'])

    sql = """
        SELECT c.id, c.first_name, c.last_name, c.email, c.birthday,
               g.name AS group_name,
               STRING_AGG(p.phone || ' [' || p.type || ']', ', ' ORDER BY p.id) AS phones
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        WHERE (%s IS NULL OR g.name = %s)
          AND (%s IS NULL OR c.email ILIKE %s)
        GROUP BY c.id, g.name
        ORDER BY """ + order_by

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (group_name, group_name, email_part, f"%{email_part}%" if email_part else None))
        rows = cur.fetchall()
        if not rows:
            print("Ничего не найдено")
            return
        for row in rows:
            print(row)


def paginated_navigation():
    """Консольная навигация next / prev / quit с использованием get_contacts_page."""
    limit = int(input("Размер страницы: ").strip())
    offset = 0
    while True:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM get_contacts_page(%s, %s)", (limit, offset))
            rows = cur.fetchall()
        print(f"OFFSET={offset}, LIMIT={limit}")
        if not rows:
            print("Нет данных на этой странице")
        else:
            for row in rows:
                print(row)
        cmd = input("Команда (next/prev/quit): ").strip().lower()
        if cmd == 'next':
            offset += limit
        elif cmd == 'prev':
            offset = max(0, offset - limit)
        elif cmd == 'quit':
            break
        else:
            print("Неизвестная команда")


def export_to_json(filename='contacts.json'):
    """Экспортирует все контакты с группой и телефонами в JSON."""
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.first_name, c.last_name, c.email, c.birthday,
                   g.name AS group_name,
                   c.created_at
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            ORDER BY c.id
            """
        )
        contacts = cur.fetchall()

        result = []
        for contact in contacts:
            cur.execute(
                "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
                (contact['id'],)
            )
            phones = cur.fetchall()
            item = dict(contact)
            item['birthday'] = item['birthday'].isoformat() if item['birthday'] else None
            item['created_at'] = item['created_at'].isoformat() if item.get('created_at') else None
            item['phones'] = [dict(p) for p in phones]
            result.append(item)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Экспорт завершён: {filename}")


def import_from_json(filename='contacts.json'):
    """Импортирует контакты из JSON, при дубле по имени спрашивает skip или overwrite."""
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)

    with get_connection() as conn, conn.cursor() as cur:
        for item in data:
            first_name = item.get('first_name')
            last_name = item.get('last_name')
            email = item.get('email')
            birthday = parse_date(item.get('birthday')) if item.get('birthday') else None
            group_name = item.get('group_name') or 'Other'
            phones = item.get('phones') or []
            phone = phones[0]['phone'] if phones else None
            phone_type = phones[0].get('type', 'mobile') if phones else 'mobile'

            exists = get_contact_id_by_name(cur, first_name, last_name)
            overwrite = False
            if exists:
                action = input(f"Контакт {first_name} уже существует. skip / overwrite? ").strip().lower()
                if action == 'skip':
                    continue
                if action != 'overwrite':
                    print("Неверная команда, выбран skip")
                    continue
                overwrite = True

            upsert_extended_contact(
                cur, first_name, last_name, email, birthday, group_name, phone, phone_type, overwrite
            )
    print("JSON импорт завершён")


def search_by_email():
    """Частичный поиск по email через ILIKE."""
    value = input("Введите часть email: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM contacts WHERE email ILIKE %s", (f"%{value}%",))
        rows = cur.fetchall()
        for row in rows:
            print(row)
        if not rows:
            print("Ничего не найдено")


def add_phone_via_procedure():
    """Вызывает новую процедуру add_phone(contact_name, phone, type)."""
    name = input("Имя контакта: ").strip()
    phone = input("Новый телефон: ").strip()
    phone_type = input("Тип телефона (home/work/mobile): ").strip().lower()
    if phone_type not in PHONE_TYPES:
        print("Неверный тип телефона")
        return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
    print("Телефон добавлен")


def move_to_group_via_procedure():
    """Вызывает новую процедуру move_to_group(contact_name, group_name)."""
    name = input("Имя контакта: ").strip()
    group_name = input("Новая группа: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
    print("Контакт перемещён в группу")


def search_via_extended_function():
    """Вызывает новую функцию search_contacts(query), которая ищет по имени, email и всем телефонам."""
    query = input("Поисковый запрос: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts(%s)", (query,))
        rows = cur.fetchall()
        if not rows:
            print("Ничего не найдено")
        else:
            for row in rows:
                print(row)


def main():
    """Главное меню расширенной телефонной книги."""
    while True:
        print("PHONEBOOK MENU")
        print("1 — импорт из CSV")
        print("2 — добавить контакт")
        print("3 — фильтр / поиск / сортировка")
        print("4 — поиск по email")
        print("5 — пагинация next/prev/quit")
        print("6 — экспорт в JSON")
        print("7 — импорт из JSON")
        print("8 — add_phone (процедура)")
        print("9 — move_to_group (процедура)")
        print("10 — search_contacts (функция)")
        print("0 — выход")

        choice = input("Выбор: ").strip()
        if choice == '1':
            import_from_csv()
        elif choice == '2':
            insert_from_console()
        elif choice == '3':
            query_contacts()
        elif choice == '4':
            search_by_email()
        elif choice == '5':
            paginated_navigation()
        elif choice == '6':
            export_to_json()
        elif choice == '7':
            import_from_json()
        elif choice == '8':
            add_phone_via_procedure()
        elif choice == '9':
            move_to_group_via_procedure()
        elif choice == '10':
            search_via_extended_function()
        elif choice == '0':
            break
        else:
            print("Неверный выбор")


if __name__ == '__main__':
    main()
