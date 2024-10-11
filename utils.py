import sqlite3

# Function to connect to the database
def connect_db():
    return sqlite3.connect('library.db')

# Function to create the database and tables if they do not exist
def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Create the students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid_code TEXT UNIQUE NOT NULL
    )
    ''')

    # Create the books table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        rfid_code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'available'
    )
    ''')

    # Create the borrowed_books table to log borrowing records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS borrowed_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,
        return_date TEXT,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (book_id) REFERENCES books(id)
    )
    ''')

    conn.commit()
    conn.close()

    print("Database and tables created successfully.")
