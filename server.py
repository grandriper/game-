"""
Game Server - Flask Backend
Handles authentication, character management, scores, and leaderboard.
Tokens expire after 24 hours. Database connections are properly closed.
"""
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import json
import os
import time
from threading import Lock

app = Flask(__name__)

# ── Token store with expiration ─────────────
# Format: { token: {"username": "...", "expires": timestamp} }
active_tokens = {}
TOKEN_LIFETIME = 24 * 3600   # 24 hours
token_lock = Lock()

def clean_expired_tokens():
    """Remove tokens that have expired."""
    now = time.time()
    with token_lock:
        expired = [t for t, data in active_tokens.items() if data["expires"] < now]
        for t in expired:
            del active_tokens[t]

# Database path
DB_PATH = 'game_server.db'

def get_db():
    """Return a new database connection. Caller must close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # allows column access by name
    return conn

def init_db():
    """Create tables and indexes if they don't exist."""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Characters table
    c.execute('''CREATE TABLE IF NOT EXISTS characters (
        char_id TEXT PRIMARY KEY,
        username TEXT,
        char_name TEXT,
        char_class TEXT,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        stats_json TEXT,
        position_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    # Scores table
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        username TEXT PRIMARY KEY,
        high_score INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 0,
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    # Add gold column if it doesn't exist (safe migration)
    try:
        c.execute('ALTER TABLE scores ADD COLUMN gold INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass   # column already exists

    # Indexes for faster lookups
    c.execute('CREATE INDEX IF NOT EXISTS idx_char_username ON characters(username)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_scores_highscore ON scores(high_score DESC)')

    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {DB_PATH}")

init_db()

# ── Helpers ─────────────────────────────────
def get_token():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    return None

def verify_token(token):
    clean_expired_tokens()
    with token_lock:
        data = active_tokens.get(token)
        if data and data["expires"] > time.time():
            return data["username"]
    return None

# ── Auth Endpoints ──────────────────────────
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        hashed = generate_password_hash(password)
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO users VALUES (?, ?, CURRENT_TIMESTAMP)', (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'User registered'}), 201

    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already taken'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'User not found'}), 401
        if not check_password_hash(row['password_hash'], password):
            return jsonify({'error': 'Invalid password'}), 401

        token = str(uuid.uuid4())
        with token_lock:
            active_tokens[token] = {
                "username": username,
                "expires": time.time() + TOKEN_LIFETIME
            }

        return jsonify({
            'status': 'success',
            'token': token,
            'username': username
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    token = get_token()
    if token:
        with token_lock:
            active_tokens.pop(token, None)
        return jsonify({'status': 'success'}), 200
    return jsonify({'error': 'Invalid token'}), 401

# ── Character Endpoints ─────────────────────
@app.route('/character/create', methods=['POST'])
def create_character():
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        char_name = data.get('char_name')
        char_class = data.get('char_class')

        if not char_name or not char_class:
            return jsonify({'error': 'Character name and class required'}), 400

        valid_classes = ['Warrior', 'Defender', 'Healer', 'Magician']
        if char_class not in valid_classes:
            return jsonify({'error': f'Invalid class. Choose from {valid_classes}'}), 400

        base_stats = {
            'Warrior': {'HP': 150, 'STR': 14, 'DEF': 10, 'MAG': 6, 'AGI': 10},
            'Defender': {'HP': 160, 'STR': 8, 'DEF': 14, 'MAG': 6, 'AGI': 8},
            'Healer': {'HP': 120, 'STR': 6, 'DEF': 8, 'MAG': 14, 'AGI': 9},
            'Magician': {'HP': 110, 'STR': 6, 'DEF': 7, 'MAG': 15, 'AGI': 11},
        }
        stats = base_stats[char_class]
        stats['level'] = 1
        stats['exp'] = 0

        char_id = str(uuid.uuid4())
        position = {'x': 0, 'y': 0, 'z': 0}

        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO characters
                     (char_id, username, char_name, char_class, stats_json, position_json)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (char_id, username, char_name, char_class,
                   json.dumps(stats), json.dumps(position)))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'char_id': char_id,
            'message': f'{char_class} {char_name} created!'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/character/<char_id>', methods=['GET'])
def get_character(char_id):
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT char_id, char_name, char_class, level, exp, stats_json, position_json
                     FROM characters WHERE char_id = ? AND username = ?''',
                  (char_id, username))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'Character not found'}), 404

        return jsonify({
            'char_id': row['char_id'],
            'char_name': row['char_name'],
            'char_class': row['char_class'],
            'level': row['level'],
            'exp': row['exp'],
            'stats': json.loads(row['stats_json']),
            'position': json.loads(row['position_json'])
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/characters', methods=['GET'])
def list_characters():
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT char_id, char_name, char_class, level FROM characters WHERE username = ?',
                  (username,))
        rows = c.fetchall()
        conn.close()

        characters = [
            {'char_id': r['char_id'], 'char_name': r['char_name'],
             'char_class': r['char_class'], 'level': r['level']}
            for r in rows
        ]
        return jsonify({'characters': characters}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/character/<char_id>/position', methods=['POST'])
def update_position(char_id):
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        x = data.get('x', 0)
        y = data.get('y', 0)
        z = data.get('z', 0)
        position = {'x': x, 'y': y, 'z': z}

        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE characters SET position_json = ?
                     WHERE char_id = ? AND username = ?''',
                  (json.dumps(position), char_id, username))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Score & Leaderboard ─────────────────────
@app.route('/score', methods=['POST'])
def update_score():
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.get_json()
        new_score = data.get('score', 0)
        new_gold = data.get('gold', 0)

        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO scores (username, high_score, gold) VALUES (?, 0, 0)',
                  (username,))
        c.execute('UPDATE scores SET gold = ? WHERE username = ?', (new_gold, username))
        c.execute('UPDATE scores SET high_score = ? WHERE username = ? AND high_score < ?',
                  (new_score, username, new_score))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT username, high_score, gold FROM scores ORDER BY high_score DESC LIMIT 10')
        rows = c.fetchall()
        conn.close()
        leaderboard = [{'username': r['username'], 'score': r['high_score'], 'gold': r['gold']}
                       for r in rows]
        return jsonify({'leaderboard': leaderboard}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/myscore', methods=['GET'])
def my_score():
    try:
        token = get_token()
        username = verify_token(token)
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT high_score, gold FROM scores WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return jsonify({'score': row['high_score'], 'gold': row['gold']}), 200
        else:
            return jsonify({'score': 0, 'gold': 0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Health Check ────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    clean_expired_tokens()
    return jsonify({
        'status': 'online',
        'active_users': len(active_tokens)
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("  GAME SERVER STARTING")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Running on: http://0.0.0.0:{port}")
    print("Production: deploy with gunicorn (HTTPS provided by your host)\n")
    app.run(host='0.0.0.0', port=port, debug=False)