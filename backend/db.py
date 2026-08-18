import sqlite3

def create_database():
    connection = sqlite3.connect("bookings.db")

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            service TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            message TEXT
        )
    """)

    connection.commit()
    connection.close()

if __name__ == "__main__":
    create_database()
    print("Database created successfully!")