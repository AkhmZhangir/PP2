# settings_manager.py — Сохранение и загрузка пользовательских настроек через settings.json

import json, os

# Путь к файлу настроек (в корне проекта рядом с main.py)
SETTINGS_FILE = "settings.json"

# Значения по умолчанию — применяются при первом запуске или при повреждённом файле
DEFAULTS = {
    "snake_color":  [80, 200, 80],  # Зелёный цвет змейки (RGB-список, не кортеж — JSON не поддерживает tuple)
    "grid_overlay": True,           # Сетка включена по умолчанию
    "sound":        False,          # Звук выключен по умолчанию
}


def load_settings():
    """
    Загружает настройки из settings.json.

    Логика:
      1. Если файл не существует — создаёт его с DEFAULT-значениями и возвращает копию.
      2. Если файл существует — читает JSON и добавляет недостающие ключи из DEFAULTS
         (защита от обновлений, когда добавляется новая настройка).
      3. Если файл повреждён (невалидный JSON) — пересоздаёт с DEFAULTS и возвращает копию.

    Возвращает словарь настроек. Всегда содержит все ключи из DEFAULTS.
    """
    if not os.path.exists(SETTINGS_FILE):
        # Первый запуск — создаём файл с настройками по умолчанию
        save_settings(DEFAULTS.copy())
        return DEFAULTS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Добавляем недостающие ключи если settings.json устарел (новые настройки)
        for k, v in DEFAULTS.items():
            if k not in data:
                data[k] = v

        return data

    except Exception:
        # Файл повреждён или нечитаем — сбрасываем к значениям по умолчанию
        save_settings(DEFAULTS.copy())
        return DEFAULTS.copy()


def save_settings(settings):
    """
    Записывает словарь настроек в settings.json.
    Вызывается в двух случаях:
      - из load_settings() при инициализации/сбросе
      - из App._ev_settings() по нажатию кнопки «Save & Back»

    indent=4 делает файл читаемым в текстовом редакторе.
    encoding="utf-8" гарантирует корректную запись на всех ОС.
    """
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)