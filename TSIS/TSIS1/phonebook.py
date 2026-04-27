# phonebook.py — TSIS

import csv
import json
from datetime import date, datetime
from connect import get_connection


def _date_serializer(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Тип {type(obj)} не сериализуем")


def _print_contacts(rows, columns=None):
    if not rows:
        print("  (нет записей)")
        return
    headers = columns or ["contact_id", "first_name", "last_name",
                          "phone", "email", "birthday", "group"]
    print("  " + " | ".join(f"{h:^15}" for h in headers))
    print("  " + "-" * (18 * len(headers)))
    for row in rows:
        print("  " + " | ".join(f"{str(v or ''):<15}" for v in row))


# ── Импорт из CSV ──────────────────────────────────────────────
def import_from_csv(filename='contacts.csv'):
    imported = 0
    with get_connection() as conn, conn.cursor() as cur, \
            open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            group_id = None
            if row.get('group'):
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                    (row['group'],))
                cur.execute("SELECT id FROM groups WHERE name = %s", (row['group'],))
                res = cur.fetchone()
                group_id = res[0] if res else None

            cur.execute("""
                INSERT INTO contacts (first_name, last_name, phone, email, birthday, group_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (phone) DO UPDATE
                    SET first_name = EXCLUDED.first_name,
                        last_name  = EXCLUDED.last_name,
                        email      = EXCLUDED.email,
                        birthday   = EXCLUDED.birthday,
                        group_id   = EXCLUDED.group_id
                RETURNING contact_id""",
                (row.get('first_name'), row.get('last_name'), row.get('phone'),
                 row.get('email') or None, row.get('birthday') or None, group_id))
            cid = cur.fetchone()[0]

            if row.get('extra_phone'):
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)"
                    " ON CONFLICT DO NOTHING",
                    (cid, row['extra_phone'], row.get('phone_type', 'mobile')))
            imported += 1
    print(f"CSV импортирован: {imported} строк.")


# ── Экспорт в JSON  ─────────────────────────────────────────────
def export_to_json(filename='contacts.json'):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.contact_id, c.first_name, c.last_name, c.phone,
                   c.email, c.birthday, g.name AS group_name
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            ORDER BY c.contact_id""")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        contacts_list = []
        for row in rows:
            contact = dict(zip(cols, row))
            cur.execute(
                "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
                (contact['contact_id'],))
            contact['phones'] = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]
            contacts_list.append(contact)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(contacts_list, f, ensure_ascii=False, indent=2,
                  default=_date_serializer)
    print(f"Экспортировано {len(contacts_list)} контактов → {filename}")


# ── Импорт из JSON ─────────────────────────────────────────────
def import_from_json(filename='contacts.json'):
    with open(filename, encoding='utf-8') as f:
        contacts_list = json.load(f)
    added = skipped = overwritten = 0
    with get_connection() as conn, conn.cursor() as cur:
        for c in contacts_list:
            cur.execute(
                "SELECT contact_id FROM contacts"
                " WHERE first_name = %s AND last_name IS NOT DISTINCT FROM %s",
                (c.get('first_name'), c.get('last_name')))
            existing = cur.fetchone()
            if existing:
                ans = input(
                    f"  '{c['first_name']} {c.get('last_name','')}'"
                    f" уже существует. [skip/overwrite]: ").strip().lower()
                if ans != 'overwrite':
                    skipped += 1; continue
                cur.execute("DELETE FROM contacts WHERE contact_id = %s", (existing[0],))
                overwritten += 1

            group_id = None
            if c.get('group_name'):
                cur.execute(
                    "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                    (c['group_name'],))
                cur.execute("SELECT id FROM groups WHERE name = %s", (c['group_name'],))
                res = cur.fetchone()
                group_id = res[0] if res else None

            cur.execute("""
                INSERT INTO contacts (first_name, last_name, phone, email, birthday, group_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING contact_id""",
                (c.get('first_name'), c.get('last_name'), c.get('phone'),
                 c.get('email'), c.get('birthday'), group_id))
            new_id = cur.fetchone()[0]
            for ph in c.get('phones', []):
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                    (new_id, ph['phone'], ph.get('type', 'mobile')))
            added += 1
    print(f"JSON импорт: добавлено={added}, перезаписано={overwritten}, пропущено={skipped}.")


# ── CRUD ───────────────────────────────────────────────────────
def insert_from_console():
    first_name = input("Имя: ").strip()
    last_name  = input("Фамилия (можно пусто): ").strip() or None
    phone      = input("Основной телефон: ").strip()
    email      = input("Email (можно пусто): ").strip() or None
    birthday   = input("День рождения (YYYY-MM-DD, можно пусто): ").strip() or None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY id")
        print("Группы:", [(g[0], g[1]) for g in cur.fetchall()])
        gid = input("group_id (или Enter пропустить): ").strip()
        group_id = int(gid) if gid else None
        cur.execute("""
            INSERT INTO contacts (first_name, last_name, phone, email, birthday, group_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING contact_id""",
            (first_name, last_name, phone, email, birthday, group_id))
        cid = cur.fetchone()[0]
        while True:
            if input("Добавить доп. телефон? (y/n): ").strip().lower() != 'y':
                break
            ep = input("  Номер: ").strip()
            et = input("  Тип (home/work/mobile): ").strip()
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                (cid, ep, et))
    print(f"Контакт добавлен (contact_id={cid}).")


def update_contact():
    by    = input("Искать по (phone/name): ").strip().lower()
    value = input("Значение: ").strip()
    field = 'phone' if by == 'phone' else 'first_name'
    print("Что обновить? 1-first_name  2-phone  3-email  4-birthday")
    ch = input("Выбор: ").strip()
    mapping = {'1': 'first_name', '2': 'phone', '3': 'email', '4': 'birthday'}
    if ch not in mapping:
        print("Неверный выбор."); return
    new_val = input("Новое значение: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"UPDATE contacts SET {mapping[ch]} = %s WHERE {field} = %s",
                    (new_val, value))
        print(f"Обновлено строк: {cur.rowcount}")


def delete_contact():
    print("Удалить по: 1-имени  2-телефону")
    ch = input("Выбор: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        if ch == '1':
            cur.execute("DELETE FROM contacts WHERE first_name = %s",
                        (input("Имя: ").strip(),))
        elif ch == '2':
            cur.execute("DELETE FROM contacts WHERE phone = %s",
                        (input("Телефон: ").strip(),))
        else:
            print("Неверный выбор."); return
        print(f"Удалено строк: {cur.rowcount}")


# ── Поиск и фильтрация ─────────────────────────────────────────
def filter_by_group():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY id")
        for g in cur.fetchall():
            print(f"  {g[0]}: {g[1]}")
        gid = input("Введите id группы: ").strip()
        cur.execute("""
            SELECT c.contact_id, c.first_name, c.last_name, c.phone,
                   c.email, c.birthday, g.name
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.group_id = %s ORDER BY c.first_name""", (gid,))
        _print_contacts(cur.fetchall())


def search_by_email():
    pattern = input("Часть email (например, gmail): ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT c.contact_id, c.first_name, c.last_name,
                   c.phone, c.email, c.birthday, g.name
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            WHERE c.email ILIKE %s ORDER BY c.first_name""",
            (f'%{pattern}%',))
        _print_contacts(cur.fetchall())


def sorted_contacts():
    print("Сортировать по: 1-name  2-birthday  3-contact_id")
    ch = input("Выбор: ").strip()
    # created_at заменён на contact_id (дата добавления = порядок id)
    order_map = {'1': 'c.first_name', '2': 'c.birthday', '3': 'c.contact_id'}
    order = order_map.get(ch, 'c.first_name')
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"""
            SELECT c.contact_id, c.first_name, c.last_name,
                   c.phone, c.email, c.birthday, g.name
            FROM contacts c
            LEFT JOIN groups g ON g.id = c.group_id
            ORDER BY {order} NULLS LAST""")
        _print_contacts(cur.fetchall())


def paginated_navigation():
    limit  = int(input("Записей на странице: ").strip())
    offset = 0
    with get_connection() as conn, conn.cursor() as cur:
        while True:
            cur.execute("SELECT * FROM get_contacts_page(%s, %s)", (limit, offset))
            rows = cur.fetchall()
            print(f"\n─── Страница {offset // limit + 1} ───")
            _print_contacts(rows)
            cmd = input("[next/prev/quit]: ").strip().lower()
            if cmd == 'next':
                if len(rows) < limit:
                    print("Последняя страница.")
                else:
                    offset += limit
            elif cmd == 'prev':
                offset = max(0, offset - limit)
            elif cmd == 'quit':
                break


# ── Процедуры и функции БД ─────────────────────────────────────
def call_add_phone():
    name  = input("Имя контакта: ").strip()
    phone = input("Номер телефона: ").strip()
    ptype = input("Тип (home/work/mobile): ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL add_phone(%s::VARCHAR, %s::VARCHAR, %s::VARCHAR)",
                    (name, phone, ptype))
    print("Телефон добавлен.")


def call_move_to_group():
    name  = input("Имя контакта: ").strip()
    group = input("Название группы (Family/Work/Friend/Other или новое): ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL move_to_group(%s::VARCHAR, %s::VARCHAR)", (name, group))
    print(f"Контакт перемещён в группу '{group}'.")


def search_via_db_function():
    pattern = input("Шаблон поиска: ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM search_contacts(%s::VARCHAR)", (pattern,))
        cols = [d[0] for d in cur.description]
        _print_contacts(cur.fetchall(), cols)


def upsert_via_procedure():
    first_name = input("Имя: ").strip()
    last_name  = input("Фамилия (можно пусто): ").strip() or None
    phone      = input("Телефон: ").strip()
    email      = input("Email (можно пусто): ").strip() or None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "CALL upsert_contact(%s::VARCHAR, %s::VARCHAR, %s::VARCHAR, %s::VARCHAR)",
            (first_name, last_name, phone, email))
    print("Upsert выполнен.")


def delete_via_procedure():
    mode = input("Удалить по (name/phone): ").strip().lower()
    name = phone = None
    if mode == 'name':
        name = input("Имя: ").strip()
    elif mode == 'phone':
        phone = input("Телефон: ").strip()
    else:
        print("Неверный режим."); return
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "CALL delete_contact_by_name_or_phone(%s::VARCHAR, %s::VARCHAR)",
            (name, phone))
    print("Удаление выполнено.")


def bulk_via_procedure():
    n = int(input("Сколько контактов: "))
    names, phones = [], []
    for _ in range(n):
        names.append(input("  Имя: ").strip())
        phones.append(input("  Телефон: ").strip())
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL bulk_upsert_contacts(%s::VARCHAR[], %s::VARCHAR[])",
                    (names, phones))
    print("Массовый insert выполнен.")


# ── Меню ───────────────────────────────────────────────────────
MENU = """
╔══════════════════════════════════════╗
║         PHONEBOOK  MENU              ║
╠══════════════════════════════════════╣
║  1  — Импорт из CSV                  ║
║  2  — Добавить контакт               ║
║  3  — Обновить контакт               ║
║  4  — Удалить контакт                ║
║─ Поиск и фильтрация ─────────────────║
║  5  — Фильтр по группе               ║
║  6  — Поиск по email                 ║
║  7  — Сортировка контактов           ║
║  8  — Постраничный просмотр          ║
║  9  — Поиск через функцию БД         ║
║─ Импорт / Экспорт ───────────────────║
║  10 — Экспорт в JSON                 ║
║  11 — Импорт из JSON                 ║
║─ Процедуры БД ───────────────────────║
║  12 — Добавить доп. телефон          ║
║  13 — Переместить в группу           ║
║  14 — Upsert (процедура)             ║
║  15 — Удалить (процедура)            ║
║  16 — Массовое добавление            ║
║──────────────────────────────────────║
║  0  — Выход                          ║
╚══════════════════════════════════════╝"""

ACTIONS = {
    '1': import_from_csv,       '2': insert_from_console,
    '3': update_contact,        '4': delete_contact,
    '5': filter_by_group,       '6': search_by_email,
    '7': sorted_contacts,       '8': paginated_navigation,
    '9': search_via_db_function,
    '10': export_to_json,       '11': import_from_json,
    '12': call_add_phone,       '13': call_move_to_group,
    '14': upsert_via_procedure, '15': delete_via_procedure,
    '16': bulk_via_procedure,
}

if __name__ == '__main__':
    while True:
        print(MENU)
        choice = input("Выбор: ").strip()
        if choice == '0':
            print("Выход."); break
        action = ACTIONS.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                print(f"Ошибка: {e}")
        else:
            print("Неверный выбор.")