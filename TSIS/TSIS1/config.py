# config.py — читает параметры подключения из database.ini
from configparser import ConfigParser
import os

def config(filename: str = 'database.ini', section: str = 'postgresql') -> dict:
    """
    Читает секцию [postgresql] из database.ini и возвращает словарь параметров.
    Пример файла database.ini:
        [postgresql]
        host=localhost
        dbname=phonebook
        user=postgres
        password=secret
        port=5432
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Файл конфигурации '{filename}' не найден.")

    parser = ConfigParser()
    parser.read(filename, encoding='utf-8')

    if not parser.has_section(section):
        raise Exception(f"Секция '{section}' не найдена в {filename}.")

    # Преобразуем список пар ключ-значение в словарь
    return dict(parser.items(section))