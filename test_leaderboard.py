#!/usr/bin/env python3
"""
Quick test: two players register, submit scores, both appear on leaderboard.

Usage (server must be running):
  cd gamer
  python test_leaderboard.py

With a remote HTTPS server:
  set GAME_SERVER_URL=https://your-server.onrender.com
  python test_leaderboard.py
"""
import sys
import uuid

import requests

from config import BASE_URL

LOGIN_URL = f"{BASE_URL}/login"
REGISTER_URL = f"{BASE_URL}/register"
SCORE_URL = f"{BASE_URL}/score"
LEADERBOARD_URL = f"{BASE_URL}/leaderboard"
STATUS_URL = f"{BASE_URL}/status"


def ok(label, passed):
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {label}")
    return passed


def register_and_login(username, password):
    requests.post(
        REGISTER_URL,
        json={"username": username, "password": password},
        timeout=10,
    )
    resp = requests.post(
        LOGIN_URL,
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    return resp.json().get("token")


def submit_score(token, score, gold):
    resp = requests.post(
        SCORE_URL,
        json={"score": score, "gold": gold},
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    return resp.status_code == 200


def get_leaderboard():
    resp = requests.get(LEADERBOARD_URL, timeout=10)
    if resp.status_code != 200:
        return []
    return resp.json().get("leaderboard", [])


def main():
    print(f"\nTesting leaderboard on: {BASE_URL}\n")

    try:
        status = requests.get(STATUS_URL, timeout=5)
        if not ok("Server online", status.status_code == 200):
            print("\nStart the server first:  python server.py\n")
            return 1
    except requests.RequestException as e:
        ok("Server reachable", False)
        print(f"  Error: {e}")
        print("\nStart the server first:  python server.py\n")
        return 1

    suffix = uuid.uuid4().hex[:6]
    player_a = f"test_player_a_{suffix}"
    player_b = f"test_player_b_{suffix}"
    password = "TestPass1"

    token_a = register_and_login(player_a, password)
    token_b = register_and_login(player_b, password)
    if not ok("Player A login", token_a is not None):
        return 1
    if not ok("Player B login", token_b is not None):
        return 1

    if not ok("Player A score submit", submit_score(token_a, 150, 50)):
        return 1
    if not ok("Player B score submit", submit_score(token_b, 300, 120)):
        return 1

    board = get_leaderboard()
    names = {entry["username"] for entry in board}
    if not ok("Leaderboard has entries", len(board) > 0):
        return 1
    if not ok(f"{player_a} on leaderboard", player_a in names):
        return 1
    if not ok(f"{player_b} on leaderboard", player_b in names):
        return 1

    print("\n  Top players:")
    for i, entry in enumerate(board[:10], 1):
        print(f"    {i}. {entry['username']}  score={entry['score']}  gold={entry.get('gold', 0)}")

    print("\nAll checks passed. Two players can see each other on the leaderboard.")
    print("\nIn-game: press L during gameplay to open the same leaderboard.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
