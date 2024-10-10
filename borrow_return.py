from mfrc522 import SimpleMFRC522
from datetime import datetime
from utils import connect_db

# Fungsi untuk autentikasi siswa
def authenticate_student():
    reader = SimpleMFRC522()

    try:
        print("Silakan scan kartu RFID siswa...")
        rfid_code = reader.read()[0]  # Membaca UID kartu RFID
        
        # Ambil data siswa berdasarkan RFID code
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM students WHERE rfid_code = ?", (rfid_code,))
        student = cursor.fetchone()

        if student:
            print(f"Siswa: {student[1]} berhasil di-autentikasi.")
            return student[0]  # Mengembalikan student_id
        else:
            print("Siswa tidak ditemukan.")
            return None
        
        conn.close()
    
    finally:
        reader.cleanup()

# Fungsi untuk memproses peminjaman atau pengembalian buku
def process_book(student_id):
    reader = SimpleMFRC522()

    try:
        print("Silakan scan stiker RFID buku...")
        rfid_code = reader.read()[0]  # Membaca UID stiker RFID

        # Ambil data buku berdasarkan RFID code
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, status FROM books WHERE rfid_code = ?", (rfid_code,))
        book = cursor.fetchone()

        if book:
            book_id, title, status = book

            if status == 'tersedia':
                # Proses peminjaman buku
                borrow_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO borrowed_books (student_id, book_id, borrow_date)
                    VALUES (?, ?, ?)
                ''', (student_id, book_id, borrow_date))

                cursor.execute("UPDATE books SET status = 'dipinjam' WHERE id = ?", (book_id,))
                print(f"Buku '{title}' berhasil dipinjam oleh siswa dengan ID {student_id}.")
            
            else:
                # Proses pengembalian buku
                return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE borrowed_books
                    SET return_date = ?
                    WHERE book_id = ? AND student_id = ? AND return_date IS NULL
                ''', (return_date, book_id, student_id))

                cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = ?", (book_id,))
                print(f"Buku '{title}' berhasil dikembalikan oleh siswa dengan ID {student_id}.")

        else:
            print("Buku tidak ditemukan.")
        
        conn.commit()
        conn.close()

    finally:
        reader.cleanup()

# Menu utama peminjaman dan pengembalian
def main():
    while True:
        print("\n1. Peminjaman atau Pengembalian Buku")
        print("2. Keluar")
        choice = input("Pilih opsi: ")

        if choice == '1':
            student_id = authenticate_student()

            if student_id:
                process
