from flask import Flask, render_template, request, redirect, session, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime
import hashlib
import time
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename

app = Flask(__name__,static_folder="assets",static_url_path="/assets")

load_dotenv()
app.secret_key = os.environ.get("ADMIN_SECRET", "dev-secret")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

STATS_DB = "assets/data/stats.db"
CONTENT_DB = "assets/data/content.db"
LIKE_COOLDOWN = 60
VIEW_COOLDOWN = 3600  # 1 hour cooldown for views
UPLOAD_FOLDER = "assets/images"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------- DB INIT ----------
def get_stats_db():
    return sqlite3.connect(STATS_DB)

def get_content_db():
    return sqlite3.connect(CONTENT_DB)

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
            CREATE TABLE IF NOT EXISTS views_ip (
                ip TEXT PRIMARY KEY,
                last_viewed INTEGER
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
    ip = request.remote_addr
    now = int(time.time())
    
    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        
        # Check if IP viewed recently
        c.execute("SELECT last_viewed FROM views_ip WHERE ip=?", (ip,))
        row = c.fetchone()
        
        should_increment = False
        if not row:
            # First time visiting
            should_increment = True
        elif now - row[0] > VIEW_COOLDOWN:
            # Cooldown expired
            should_increment = True
            
        if should_increment:
            c.execute("UPDATE stats SET views = views + 1 WHERE id=1")
            c.execute("INSERT OR REPLACE INTO views_ip (ip, last_viewed) VALUES (?,?)", (ip, now))
            conn.commit()

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
        with sqlite3.connect(STATS_DB) as conn:
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

@app.route("/api/achievements")
def achievements():
    db = get_content_db()
    cur = db.cursor()

    cur.execute("""
        SELECT title, description, icon, cover_image, date
        FROM achievements
        WHERE visible = 1
        ORDER BY date DESC
    """)

    rows = cur.fetchall()
    db.close()

    return jsonify([
        {
            "title": r[0],
            "description": r[1],
            "icon": r[2],
            "cover": r[3],
            "date": r[4]
        } for r in rows
    ])

@app.route("/api/projects")
def get_projects():
    status = request.args.get("status")  # completed | ongoing (optional)

    with open("assets/data/projects.json", "r", encoding="utf-8") as f:
        projects = json.load(f)

    # 🔥 SORT BY RANK (ascending)
    projects.sort(key=lambda p: p.get("rank", float("inf")))

    return jsonify([
        {
            "slug": p["id"],
            "title": p["title"],
            "shortDesc": p["shortDesc"],
            "details": p["details"],
            "tech": p.get("tech", []),
            "media": p.get("media", {}),
            "github": p.get("links", {}).get("github"),
            "demo": p.get("links", {}).get("demo")
        }
        for p in projects
    ])

# ------------Admin Parts-------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form["password"]

        if hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return render_template("admin/login.html", error="Invalid password")

    return render_template("admin/login.html")

def admin_required():
    if not session.get("admin"):
        return redirect("/admin/login")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")
    return render_template("admin/dashboard.html")

@app.route("/admin/achievements")
def admin_achievements():
    if not session.get("admin"):
        return redirect("/admin/login")

    db = get_content_db()
    rows = db.execute(
        "SELECT id, title, description, icon, cover_image, visible FROM achievements"
    ).fetchall()
    db.close()

    return render_template("admin/achievements.html", achievements=rows)

@app.route("/admin/achievements/add", methods=["POST"])
def add_achievement():
    if not session.get("admin"):
        return "Unauthorized", 401

    data = request.form
    db = get_content_db()
    db.execute(
        "INSERT INTO achievements (title, description, icon, date) VALUES (?, ?, ?, ?)",
        (data["title"], data["description"], data["icon"], data["date"])
    )
    db.commit()
    db.close()

    return redirect("/admin/achievements")

@app.route("/admin/achievements/toggle/<int:id>", methods=["POST"])
def toggle_achievement(id):
    if not session.get("admin"):
        return "Unauthorized", 401

    db = get_content_db()
    db.execute(
        "UPDATE achievements SET visible = NOT visible WHERE id = ?", (id,)
    )
    db.commit()
    db.close()

    return redirect("/admin/achievements")

@app.route("/admin/comments")
def admin_comments():
    if not session.get("admin"):
        return redirect("/admin/login")

    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, comment, timestamp FROM comments ORDER BY id DESC")
        rows = c.fetchall()

    return render_template("admin/comments.html", comments=rows)

@app.route("/admin/comments/delete/<int:id>", methods=["POST"])
def delete_comment(id):
    if not session.get("admin"):
        return "Unauthorized", 401

    with sqlite3.connect(STATS_DB) as conn:
        conn.execute("DELETE FROM comments WHERE id = ?", (id,))

    return redirect("/admin/comments")

@app.route("/resume")
def serve_resume():
    try:
        return send_from_directory("assets/docs", "resume.pdf", as_attachment=False)
    except:
        return "Resume not available", 404

@app.route("/admin/resume", methods=["GET", "POST"])
def admin_resume():
    if not session.get("admin"):
        return redirect("/admin/login")
    
    success_msg = None
    if request.method == "POST":
        file = request.files.get("resume")
        if file and file.filename.endswith(".pdf"):
            os.makedirs("assets/docs", exist_ok=True)
            file.save(os.path.join("assets/docs", "resume.pdf"))
            success_msg = "Resume uploaded successfully!"
    
    return render_template("admin/resume.html", success=success_msg)

# Admin Ends

