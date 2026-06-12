# Save/Load System — one save file per account
import copy
import json
import os
import re

from config import data_dir
from settings import UPGRADES_DEFAULTS

SAVES_DIR = os.path.join(data_dir(), "saves")


def _safe_username(username):
    """Filesystem-safe username for save filenames."""
    safe = re.sub(r"[^\w\-]", "_", username.strip())
    return safe or "player"


def _save_path(username):
    os.makedirs(SAVES_DIR, exist_ok=True)
    return os.path.join(SAVES_DIR, f"{_safe_username(username)}.json")


def default_progress():
    return {
        "gold": 0,
        "upgrades": copy.deepcopy(UPGRADES_DEFAULTS),
        "high_score": 0,
        "tutorial_done": False,
    }


def load_game(username):
    """Load progress for a specific account."""
    if not username:
        return default_progress()

    path = _save_path(username)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "upgrades" not in data:
                data["upgrades"] = copy.deepcopy(UPGRADES_DEFAULTS)
            return data
    except Exception as e:
        print(f"Load error for {username}: {e}")

    return default_progress()


def save_game(data, username):
    """Save progress for a specific account."""
    if not username:
        return False

    try:
        path = _save_path(username)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Save error for {username}: {e}")
        return False


def migrate_legacy_save(main_username="abdallah"):
    """
    One-time migration: move old shared save.json to the main account only.
    Other accounts always start with fresh defaults.
    """
    legacy = os.path.join(data_dir(), "save.json")
    if not os.path.exists(legacy) or not main_username:
        return

    dest = _save_path(main_username)
    if os.path.exists(dest):
        return

    try:
        with open(legacy, "r", encoding="utf-8") as f:
            data = json.load(f)
        os.makedirs(SAVES_DIR, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Migrated save.json -> saves/{_safe_username(main_username)}.json")
    except Exception as e:
        print(f"Legacy save migration failed: {e}")
