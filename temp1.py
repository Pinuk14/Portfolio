import sqlite3

STATS_DB = "assets/data/stats.db"

def reset_stats():
    with sqlite3.connect(STATS_DB) as conn:
        c = conn.cursor()

        # Reset views and likes
        c.execute("""
            UPDATE stats
            SET views = 0,
                likes = 0
            WHERE id = 1
        """)

        # Clear IP-based like cooldowns
        c.execute("DELETE FROM likes_ip")

        conn.commit()

    print("✅ Views, likes, and IP cooldowns reset successfully.")

if __name__ == "__main__":
    reset_stats()
