import sqlite3

def init_db():

    conn = sqlite3.connect("loans.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
             CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    income REAL,
                    age INTEGER,
                    loan_amount REAL,
                    credit_score INTEGER,
                    decision TEXT,
                    reason TEXT
                )
    """)

if __name__ == "__main__":
    init_db()
    print("Database initialized")