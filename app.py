from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

import time


app = Flask(
    __name__,
    static_folder="assets",
    static_url_path="/assets"
)

STATS_DB = "db/stats.db"
CONTENT_DB = "db/content.db"
LIKE_COOLDOWN = 60

# ---------- DB INIT ----------
def init_db():
    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS likes_ip (
                ip TEXT PRIMARY KEY,
                last_liked INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                comment TEXT,
                timestamp TEXT
            )
        """)
        c.execute("INSERT OR IGNORE INTO stats (id, views, likes) VALUES (1,0,0)")
        conn.commit()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def index():
    increment_views()
    return send_from_directory(".", "index.html")

def increment_views():
    with sqlite3.connect(STATS_DB) as conn:
        conn.execute("UPDATE stats SET views = views + 1 WHERE id=1")

@app.route("/assets/data/<path:filename>")
def data_files(filename):
    return send_from_directory("assets/data", filename)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT views, likes FROM stats WHERE id=1")
        views, likes = c.fetchone()
    return jsonify({"views": views, "likes": likes})

@app.route("/api/like", methods=["POST"])
def like():
    ip = request.remote_addr
    now = int(time.time())

    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT last_liked FROM likes_ip WHERE ip=?", (ip,))
        row = c.fetchone()
        if row and now - row[0] < LIKE_COOLDOWN:
            return jsonify({"status": "blocked"}), 429
        # update like count
        c.execute("UPDATE stats SET likes = likes + 1 WHERE id=1")
        # update ip timestamp
        c.execute(
            "INSERT OR REPLACE INTO likes_ip (ip, last_liked) VALUES (?,?)",
            (ip, now)
        )
        conn.commit()

    return jsonify({"status": "ok"})

@app.route("/api/comments", methods=["GET", "POST"])
def comments():
    if request.method == "POST":
        data = request.json
        with sqlite3.connect(STATS_DBDB) as conn:
            conn.execute(
                "INSERT INTO comments (name, comment, timestamp) VALUES (?,?,?)",
                (data["name"], data["comment"], datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
        return jsonify({"status": "saved"})

    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT name, comment, timestamp FROM comments ORDER BY id DESC")
        rows = c.fetchall()

    return jsonify([
        {"name": r[0], "comment": r[1], "timestamp": r[2]} for r in rows
    ])

if __name__ == "__main__":
    app.run(port=5500, debug=True)
