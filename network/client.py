# API Client
import requests
from settings import *
from config import BASE_URL as _BASE_URL

def try_login(username, password):
    """Attempt login. Returns token on success, None on failure."""
    try:
        resp = requests.post(LOGIN_URL, json={'username': username, 'password': password}, timeout=30)
        if resp.status_code == 200:
            return resp.json().get('token')
    except Exception as e:
        print(f"Login error ({_BASE_URL}): {e}")
    return None

def try_register(username, password):
    """Attempt registration. Returns True on success."""
    try:
        resp = requests.post(REGISTER_URL, json={'username': username, 'password': password}, timeout=30)
        return resp.status_code == 201
    except Exception as e:
        print(f"Register error: {e}")
    return False

def submit_score(token, score, gold):
    """Submit score and gold to server."""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(SCORE_URL, json={'score': score, 'gold': gold}, headers=headers, timeout=3)
        return resp.status_code == 200
    except Exception as e:
        print(f"Score submission error: {e}")
    return False

def get_leaderboard():
    """Get top 10 leaderboard."""
    try:
        resp = requests.get(LEADERBOARD_URL, timeout=3)
        if resp.status_code == 200:
            return resp.json().get('leaderboard', [])
    except Exception as e:
        print(f"Leaderboard error: {e}")
    return []

def get_my_score(token):
    """Get current user's score and gold. Returns (score, gold)."""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.get(MYSCORE_URL, headers=headers, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('score', 0), data.get('gold', 0)
    except Exception as e:
        print(f"Score fetch error: {e}")
    return 0, 0

def check_server_status():
    """Check if server is online (long timeout for cloud cold starts)."""
    try:
        resp = requests.get(STATUS_URL, timeout=30)
        return resp.status_code == 200
    except Exception:
        return False
