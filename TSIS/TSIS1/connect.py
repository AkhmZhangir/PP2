# connect.py — единственная точка получения соединения с PostgreSQL
import psycopg2
from config import config


def get_connection():
    """
    Открывает и возвращает соединение psycopg2.
    Все остальные модули импортируют только эту функцию,
    чтобы параметры подключения хранились в одном месте.
    """
    params = config()                   # читаем database.ini
    return psycopg2.connect(**params)   # возвращаем объект соединения