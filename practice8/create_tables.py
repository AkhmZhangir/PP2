import psycopg2
from config import config


def create_tables():
    commands = [
        """
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name  VARCHAR(100),
            phone      VARCHAR(30) UNIQUE NOT NULL,
            email      VARCHAR(100)
        )
        """
    ]

    try:
        params = config()
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cur:
                for command in commands:
                    cur.execute(command)
        print("Table created successfully")
    except Exception as error:
        print(error)


if __name__ == '__main__':
    create_tables()