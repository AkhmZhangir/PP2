import json, os

SETTINGS_FILE = "settings.json"
DEFAULTS = {
    "snake_color": [80, 200, 80],
    "grid_overlay": True,
    "sound": False,
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULTS.copy())
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in DEFAULTS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        save_settings(DEFAULTS.copy())
        return DEFAULTS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)