from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD

# Inisialisasi LCD (ganti 0x27 dengan alamat I2C LCD Anda)
lcd = CharLCD('PCF8574', 0x27)

# Inisialisasi RFID Reader
reader = SimpleMFRC522()

def clear_lcd():
    """Membersihkan layar LCD."""
    lcd.clear()

def display_lcd_message(line1, line2="", duration=2):
    """Menampilkan pesan di LCD 16x2."""
    clear_lcd()
    lcd.write_string(line1)
    if line2:
        lcd.crlf()  # Pindah ke baris kedua
        lcd.write_string(line2)
    time.sleep(duration)  # Tampilkan pesan selama beberapa detik
    clear_lcd()

def read_rfid_card():
    """Membaca kartu RFID dan mengembalikan UID."""
    try:
        print("Please scan your RFID card...")
        display_lcd_message("Scan your card")
        rfid_code, text = reader.read()  # Baca UID kartu siswa
        return rfid_code
    except Exception as e:
        print(f"Error reading RFID: {e}")
        display_lcd_message("Error Reading Card")
        return None

def wait_until_card_removed():
    """Menunggu sampai kartu RFID dilepas dengan deteksi yang lebih stabil."""
    print("Waiting for card removal...")
    display_lcd_message("Please Remove Card")
    
    no_card_count = 0  # Hitung berapa kali tidak ada kartu terdeteksi berturut-turut
    threshold = 3  # Ambang batas berapa kali pembacaan kosong berturut-turut sebelum kita anggap kartu dilepas
    
    while True:
        try:
            # Coba baca kartu secara non-blocking
            rfid_code, text = reader.read_no_block()

            if rfid_code is None:
                # Jika tidak ada kartu terbaca, tambahkan hitungan tidak ada kartu
                no_card_count += 1
                print(f"No card detected, count: {no_card_count}")
                display_lcd_message("Processing...")
            else:
                # Jika kartu terbaca kembali, reset hitungan
                no_card_count = 0
                print("Card still detected. Waiting for removal...")
                display_lcd_message("Card Still Detected")

            # Jika kartu tidak terbaca selama 'threshold' kali berturut-turut, keluar dari loop
            if no_card_count >= threshold:
                print("Card removed.")
                display_lcd_message("Card Removed")
                break

            # Jeda untuk memastikan tidak terlalu cepat membaca ulang
            time.sleep(0.5)

        except Exception as e:
            print(f"Error while waiting for card removal: {e}")
            display_lcd_message("Error Removing Card")
            break

def process_borrow_return(student_id):
    """Proses peminjaman atau pengembalian buku."""
    try:
        print("Please scan the book's RFID tag...")
        display_lcd_message("Scan the Book")
        rfid_code = reader.read()[0]  # Membaca UID buku

        conn = connect_db()
        cursor = conn.cursor()

        # Cek status buku di database berdasarkan RFID tag
        cursor.execute("SELECT id, title, status FROM books WHERE rfid_code = ?", (rfid_code,))
        book = cursor.fetchone()

        if book:
            book_id, title, status = book

            if status == 'tersedia':
                # Proses peminjaman buku
                borrow_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO borrowed_books (student_id, book_id, borrow_date)
                    VALUES (?, ?, ?)
                ''', (student_id, book_id, borrow_date))
                cursor.execute("UPDATE books SET status = 'dipinjam' WHERE id = ?", (book_id,))
                conn.commit()
                print(f"Book '{title}' borrowed successfully.")
                display_lcd_message("Borrow Successful", f"Book: {title}")
            elif status == 'dipinjam':
                # Proses pengembalian buku
                return_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE borrowed_books SET return_date = ?
                    WHERE book_id = ? AND student_id = ? AND return_date IS NULL
                ''', (return_date, book_id, student_id))
                cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = ?", (book_id,))
                conn.commit()
                print(f"Book '{title}' returned successfully.")
                display_lcd_message("Return Successful", f"Book: {title}")
            else:
                print(f"Error: Unknown book status '{status}'.")
                display_lcd_message("Error: Unknown", "Book Status")
        else:
            print("Error: Book not found.")
            display_lcd_message("Error: Book", "Not Found")

        conn.close()

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_lcd_message("Error", "Borrow/Return")

def borrow_return():
    """Fungsi utama untuk proses peminjaman/pengembalian buku."""
    # Baca kartu RFID siswa
    student_rfid = read_rfid_card()
    
    if student_rfid is None:
        print("Error: No card detected.")
        display_lcd_message("No Card Detected")
        return

    # Verifikasi apakah siswa terdaftar di database
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students WHERE rfid_code = ?", (student_rfid,))
    student = cursor.fetchone()
    conn.close()

    if student:
        student_id, student_name = student
        print(f"Authenticated student: {student_name}")
        display_lcd_message("Student Verified", student_name)

        # Tunggu hingga kartu siswa dilepas
        wait_until_card_removed()

        # Minta siswa untuk scan buku
        process_borrow_return(student_id)
    else:
        print("Error: Student not found.")
        display_lcd_message("Student Not Found")


if __name__ == '__main__':
    try:
        borrow_return()
    finally:
        GPIO.cleanup()  # Bersihkan GPIO saat program selesai
