# db_setup.py
import sqlite3

def create_tables():
    conn = sqlite3.connect("uk49s.db")
    cursor = conn.cursor()

    # Create draws table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS draws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        draw_type TEXT NOT NULL,
        numbers TEXT NOT NULL,
        booster INTEGER
    )
    """)

    # Create numbers table (normalized for analysis)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draw_id INTEGER NOT NULL,
        number INTEGER NOT NULL,
        position INTEGER,
        FOREIGN KEY (draw_id) REFERENCES draws (id)
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database and tables created successfully!")

if __name__ == "__main__":
    create_tables()
