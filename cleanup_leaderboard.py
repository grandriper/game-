#!/usr/bin/env python3
"""Remove test accounts from the local leaderboard database."""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_server.db")


def main():
    if not os.path.exists(DB_PATH):
        print(f"No database at {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT username FROM scores WHERE username LIKE 'test_player_%'")
    test_users = [row[0] for row in c.fetchall()]

    if not test_users:
        print("No test players found on leaderboard.")
    else:
        for name in test_users:
            c.execute("DELETE FROM scores WHERE username = ?", (name,))
            c.execute("DELETE FROM users WHERE username = ?", (name,))
            print(f"Removed: {name}")
        conn.commit()
        print(f"Cleaned {len(test_users)} test account(s).")

    c.execute(
        "SELECT username, high_score, gold FROM scores ORDER BY high_score DESC LIMIT 10"
    )
    print("\nCurrent top 10:")
    for i, row in enumerate(c.fetchall(), 1):
        print(f"  {i}. {row[0]}  score={row[1]}  gold={row[2]}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
