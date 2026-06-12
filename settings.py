# Game Settings & Configuration

# Window
WIDTH = 1200
HEIGHT = 800
FPS = 60
TITLE = "The Crown of Externality"
VERSION = "0.1.0"

# Colors
BG = (15, 15, 30)
WHITE = (255, 255, 255)
ACTIVE = (0, 200, 255)
INACTIVE = (80, 80, 80)
BALL = (255, 80, 80)
COIN = (255, 215, 0)
GREEN = (80, 255, 80)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
PLAYER = (0, 220, 255)
BULLET = (180, 255, 180)

# Network (HTTPS in production — set server_url in server_config.json)
from config import BASE_URL

LOGIN_URL = f'{BASE_URL}/login'
REGISTER_URL = f'{BASE_URL}/register'
SCORE_URL = f'{BASE_URL}/score'
LEADERBOARD_URL = f'{BASE_URL}/leaderboard'
MYSCORE_URL = f'{BASE_URL}/myscore'
STATUS_URL = f'{BASE_URL}/status'

# File Paths
SAVE_FILE = 'save.json'
ASSETS_DIR = 'assets'
MUSIC_DIR = 'music'

# Music tracks
MUSIC_MENU = ["music/start1.mp3", "music/start2.mp3"]
MUSIC_GAME = "music/game.wav"
MUSIC_BOSS = {
    1: "music/boss.mp3",      # boss1.png
    2: "music/boss1.mp3",     # boss2.png
    3: "music/boss1.mp3",     # boss3.png (reuse)
    4: "music/boss1.mp3",     # boss4.png (reuse)
    5: "music/boss1.mp3",     # boss5.png (reuse)
}

# Sound effects
SFX_BULLET = "music/bulit_shot.mp3"

# Game mechanics
HITBOX_W = 180
HITBOX_H = 120
SPRITE_W = 160
SPRITE_H = 120
SHIELD_SPRITE_W = 200
SHIELD_SPRITE_H = 160
OFFSET_X = (HITBOX_W - SPRITE_W) // 2
OFFSET_Y = (HITBOX_H - SPRITE_H) // 2
SHIELD_OFFSET_X = (HITBOX_W - SHIELD_SPRITE_W) // 2
SHIELD_OFFSET_Y = (HITBOX_H - SHIELD_SPRITE_H) // 2
ANIM_SPEED = 10
BULLET_SPEED = 7
BOSS_DEFEATED_SCORE = 500
BOSS_LEVELS = [3, 6, 9, 12, 15]

# Upgrades
UPGRADES_DEFAULTS = {
    "speed": {"level": 0, "cost": 100, "effect": 1},
    "fire_rate": {"level": 0, "cost": 150, "effect": -2},
    "shield": {"level": 0, "cost": 200, "effect": 1},
}
