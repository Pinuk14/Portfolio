import json
import sqlite3
from datetime import datetime
from pathlib import Path

# ==========================
# CONFIG
# ==========================
JSON_FILE = Path("assets/data/projects.json")
DB_FILE = Path("assets/data/content.db")

# ==========================
# DB SETUP
# ==========================
def get_db():
    return sqlite3.connect(DB_FILE)

def ensure_table():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE,
        title TEXT,
        short_desc TEXT,
        details TEXT,
        tech TEXT,
        media TEXT,
        status TEXT,
        github TEXT,
        demo TEXT,
        visible INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# ==========================
# JSON → DB
# ==========================
def json_to_db():
    ensure_table()

    if not JSON_FILE.exists():
        print("❌ JSON file not found")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        projects = json.load(f)

    conn = get_db()
    cur = conn.cursor()
    inserted = 0

    for p in projects:
        try:
            cur.execute("""
            INSERT INTO projects (
                slug, title, short_desc, details,
                tech, media, status,
                github, demo, visible, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                p.get("id"),
                p.get("title"),
                p.get("shortDesc"),
                p.get("details"),
                json.dumps(p.get("tech", [])),
                json.dumps(p.get("media", {})),
                "completed",
                p.get("links", {}).get("github"),
                p.get("links", {}).get("demo"),
                datetime.utcnow().isoformat()
            ))

            inserted += 1

        except sqlite3.IntegrityError:
            print(f"⚠️ Skipped duplicate: {p.get('id')}")

    conn.commit()
    conn.close()

    print(f"✅ Imported {inserted} projects into DB")

# ==========================
# DB → JSON
# ==========================
def db_to_json():
    ensure_table()

    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT slug, title, short_desc, details,
               tech, media, status, github, demo
        FROM projects
        WHERE visible = 1
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    projects = []

    for r in rows:
        projects.append({
            "id": r[0],
            "title": r[1],
            "shortDesc": r[2],
            "details": r[3],
            "tech": json.loads(r[4] or "[]"),
            "media": json.loads(r[5] or "{}"),
            "status": r[6],
            "links": {
                "github": r[7],
                "demo": r[8]
            }
        })

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=4, ensure_ascii=False)

    print(f"✅ Exported {len(projects)} projects to JSON")

# ==========================
# MENU
# ==========================
def main():
    print("\n=== Project Migration Tool ===")
    print("1️⃣  JSON → DB")
    print("2️⃣  DB → JSON")
    print("0️⃣  Exit")

    choice = input("\nChoose option: ").strip()

    if choice == "1":
        json_to_db()
    elif choice == "2":
        db_to_json()
    else:
        print("👋 Exit")

if __name__ == "__main__":
    main()
