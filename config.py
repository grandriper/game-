# Server URL configuration (local dev vs Steam/production HTTPS)
import json
import os
import sys

DEFAULT_SERVER_URL = "http://localhost:5000"
CONFIG_FILENAME = "server_config.json"


def _app_dir():
    """Directory containing game.py or the built .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def data_dir():
    """Writable data directory (saves, config) — always beside the .exe when frozen."""
    return _app_dir()


def resource_path(relative):
    """
    Resolve bundled assets (sprites, music inside PyInstaller _MEIPASS)
    or files sitting next to game.py / the .exe.
    """
    if getattr(sys, "frozen", False):
        bundle = getattr(sys, "_MEIPASS", _app_dir())
        bundled = os.path.join(bundle, relative)
        if os.path.exists(bundled):
            return bundled
    local = os.path.join(_app_dir(), relative)
    return local


ASSETS_DIR = "assets"


def asset_path(filename):
    """Resolve a PNG/sprite path inside the assets folder."""
    return resource_path(os.path.join(ASSETS_DIR, filename))


def _config_path():
    return os.path.join(data_dir(), CONFIG_FILENAME)


def load_server_url():
    """
    Resolve server URL in priority order:
    1. GAME_SERVER_URL environment variable
    2. server_config.json next to the game / exe
    3. localhost fallback for development
    """
    env_url = os.environ.get("GAME_SERVER_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    config_path = _config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            url = data.get("server_url", "").strip()
            if url:
                return url.rstrip("/")
        except Exception as e:
            print(f"Warning: could not read {config_path}: {e}")

    return DEFAULT_SERVER_URL


BASE_URL = load_server_url()
