import sqlite3

# Fungsi untuk membuat koneksi ke database
def connect_db():
    return sqlite3.connect('database/library.db')

# Fungsi untuk membuat database dan tabel jika belum ada
def create_database():
    conn = connect_db()
    cursor = conn.cursor()

    # Membuat tabel students (siswa)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        rfid_code TEXT UNIQUE NOT NULL
    )
    ''')

    # Membuat tabel books (buku)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        rfid_code TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'tersedia'
    )
    ''')

    # Membuat tabel borrowed_books (catatan peminjaman)
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

    print("Database dan tabel berhasil dibuat.")
