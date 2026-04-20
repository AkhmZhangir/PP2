import csv
import psycopg2
from config import config


def get_connection():
    params = config()
    return psycopg2.connect(**params)


def import_from_csv(filename='contacts.csv'):
    with get_connection() as conn, conn.cursor() as cur, \
            open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute(
                """
                INSERT INTO contacts (first_name, last_name, phone, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (phone) DO UPDATE
                SET first_name = EXCLUDED.first_name,
                    last_name  = EXCLUDED.last_name,
                    email      = EXCLUDED.email
                """,
                (row.get('first_name'),
                 row.get('last_name'),
                 row.get('phone'),
                 row.get('email'))
            )
    print("CSV импортирован")


def insert_from_console():
    first_name = input("Имя: ").strip()
    last_name = input("Фамилия (можно пусто): ").strip() or None
    phone = input("Телефон: ").strip()
    email = input("Email (можно пусто): ").strip() or None

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contacts (first_name, last_name, phone, email)
            VALUES (%s, %s, %s, %s)
            """,
            (first_name, last_name, phone, email)
        )
    print("Контакт добавлен")


def update_contact():
    phone_or_name = input("По какому полю искать (phone/name): ").strip().lower()
    value = input("Значение для поиска: ").strip()

    field = 'phone' if phone_or_name == 'phone' else 'first_name'

    print("Что обновляем?")
    print("1 — first_name")
    print("2 — phone")
    choice = input("Выбор: ").strip()

    if choice == '1':
        new_value = input("Новое имя: ").strip()
        set_clause = "first_name = %s"
    elif choice == '2':
        new_value = input("Новый телефон: ").strip()
        set_clause = "phone = %s"
    else:
        print("Неверный выбор")
        return

    with get_connection() as conn, conn.cursor() as cur:
        query = f"UPDATE contacts SET {set_clause} WHERE {field} = %s"
        cur.execute(query, (new_value, value))
        print("Обновлено строк:", cur.rowcount)


def query_contacts():
    print("Фильтры:")
    print("1 — по имени (точное совпадение)")
    print("2 — по префиксу телефона")
    choice = input("Выбор: ").strip()

    with get_connection() as conn, conn.cursor() as cur:
        if choice == '1':
            name = input("Имя: ").strip()
            cur.execute(
                "SELECT * FROM contacts WHERE first_name = %s",
                (name,)
            )
        elif choice == '2':
            prefix = input("Префикс телефона: ").strip()
            cur.execute(
                "SELECT * FROM contacts WHERE phone LIKE %s",
                (prefix + '%',)
            )
        else:
            print("Неверный выбор")
            return

        rows = cur.fetchall()
        if not rows:
            print("Ничего не найдено")
        else:
            for r in rows:
                print(r)


def delete_contact():
    print("Удалить по:")
    print("1 — имени")
    print("2 — телефону")
    choice = input("Выбор: ").strip()

    with get_connection() as conn, conn.cursor() as cur:
        if choice == '1':
            name = input("Имя: ").strip()
            cur.execute(
                "DELETE FROM contacts WHERE first_name = %s",
                (name,)
            )
        elif choice == '2':
            phone = input("Телефон: ").strip()
            cur.execute(
                "DELETE FROM contacts WHERE phone = %s",
                (phone,)
            )
        else:
            print("Неверный выбор")
            return

        print("Удалено строк:", cur.rowcount)


def search_via_db_function():
    pattern = input("Введите шаблон (часть имени/фамилии/телефона): ").strip()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM get_contacts_by_pattern(%s)", (pattern,))
        rows = cur.fetchall()
        if not rows:
            print("Ничего не найдено")
        else:
            for r in rows:
                print(r)
def paginated_via_db_function():
    limit = int(input("Сколько строк на странице (LIMIT): "))
    offset = int(input("OFFSET (сколько пропустить): "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM get_contacts_page(%s, %s)", (limit, offset))
        rows = cur.fetchall()
        if not rows:
            print("Больше строк нет")
        else:
            for r in rows:
                print(r)
def upsert_via_procedure():
    first_name = input("Имя: ").strip()
    last_name  = input("Фамилия (можно пусто): ").strip() or None
    phone      = input("Телефон: ").strip()
    email      = input("Email (можно пусто): ").strip() or None

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL upsert_contact(%s, %s, %s, %s)",
                    (first_name, last_name, phone, email))
    print("Upsert через БД выполнен")
def delete_via_procedure():
    mode = input("Удалить по (name/phone): ").strip().lower()
    name = phone = None
    if mode == 'name':
        name = input("Имя: ").strip()
    elif mode == 'phone':
        phone = input("Телефон: ").strip()
    else:
        print("Неверный режим")
        return

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "CALL delete_contact_by_name_or_phone(%s, %s)",
            (name, phone)
        )
    print("Удаление через БД выполнено")
def bulk_via_procedure():
    n = int(input("Сколько контактов добавить: "))
    names = []
    phones = []
    for _ in range(n):
        names.append(input("Имя: ").strip())
        phones.append(input("Телефон: ").strip())

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("CALL bulk_upsert_contacts(%s, %s)", (names, phones))
    print("Массовый insert через БД выполнен")


def main():
    while True:
        print("\nPHONEBOOK MENU")
        print("1 — импорт из CSV")
        print("2 — добавить контакт")
        print("3 — обновить контакт")
        print("4 — найти контакты")
        print("5 — удалить контакт")
        print("6 — поиск (функция в БД)")
        print("7 — показать страницу контактов (функция в БД)")
        print("8 — upsert (процедура в БД)")
        print("9 — удалить (процедура в БД)")
        print("10 — массовое добавление (процедура в БД)")
        print("0 — выход")

        choice = input("Выбор: ").strip()
        if choice == '1':
            import_from_csv()
        elif choice == '2':
            insert_from_console()
        elif choice == '3':
            update_contact()
        elif choice == '4':
            query_contacts()
        elif choice == '5':
            delete_contact()
        elif choice == '6':
            search_via_db_function()
        elif choice == '7':
            paginated_via_db_function()
        elif choice == '8':
            upsert_via_procedure()
        elif choice == '9':
            delete_via_procedure()
        elif choice == '10':
            bulk_via_procedure()
        elif choice == '0':
            break
        else:
            print("Неверный выбор")


if __name__ == "__main__":
    main()