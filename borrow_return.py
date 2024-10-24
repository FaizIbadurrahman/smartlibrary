from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD

# Inisialisasi LCD 16x2 dengan alamat I2C (misal: 0x27)
lcd = CharLCD('PCF8574', 0x27)

# Inisialisasi RFID Reader
reader = SimpleMFRC522()

def clear_lcd():
    """Membersihkan layar LCD."""
    lcd.clear()

def center_text(text, width=16):
    """Menyusun teks agar ditampilkan di tengah layar LCD 16x2."""
    if len(text) < width:
        padding = (width - len(text)) // 2
        return ' ' * padding + text + ' ' * padding
    return text[:width]  # Jika lebih dari 16 karakter, potong

def display_lcd_message(line1, line2=""):
    """Menampilkan pesan di LCD 16x2 dengan teks yang ditengah."""
    lcd.clear()  # Bersihkan layar
    lcd.write_string(center_text(line1))  # Tampilkan baris pertama ditengah
    if line2:
        lcd.crlf()  # Pindah ke baris kedua
        lcd.write_string(center_text(line2))  # Tampilkan baris kedua ditengah

def scroll_text(line, text, delay=0.3):
    """Scrolling text pada baris tertentu jika panjangnya lebih dari 16 karakter."""
    lcd.cursor_pos = (line, 0)
    
    # Jika teks lebih pendek dari atau sama dengan 16 karakter, tampilkan langsung
    if len(text) <= 16:
        lcd.write_string(text)
        return

    # Scrolling jika teks lebih dari 16 karakter
    # Tampilkan teks pertama (16 karakter pertama) langsung
    lcd.write_string(text[:16])
    time.sleep(delay)
    
    # Mulai scroll teks
    for i in range(1, len(text) - 15):  # Loop untuk scroll
        lcd.cursor_pos = (line, 0)  # Set baris yang akan di-scroll
        lcd.write_string(text[i:i + 16])  # Geser window teks sepanjang 16 karakter
        time.sleep(delay)  # Delay untuk memberikan efek scroll

def read_rfid_card():
    """Membaca kartu RFID dan mengembalikan UID."""
    try:
        print("Awaiting RFID input...")
        display_lcd_message("Scan your ID")
        rfid_code, text = reader.read()  # Baca UID kartu siswa
        return rfid_code
    except Exception as e:
        print(f"Error reading RFID: {e}")
        display_lcd_message("Error Reading", "Card Data")
        return None

def wait_until_card_removed():
    """Menunggu sampai kartu RFID dilepas dengan deteksi yang lebih stabil."""
    print("Please remove the card...")
    display_lcd_message("Please", "Remove Card")
    
    no_card_count = 0
    threshold = 3  # Jika 3 kali tidak ada kartu, anggap kartu dilepas
    
    while True:
        try:
            rfid_code, text = reader.read_no_block()
            if rfid_code is None:
                no_card_count += 1
                print(f"No card detected, count: {no_card_count}")
            else:
                no_card_count = 0
                print("Card still detected.")
            
            if no_card_count >= threshold:
                print("Card removed.")
                display_lcd_message("Card Removed")
                break
            time.sleep(0.5)

        except Exception as e:
            print(f"Error while waiting for card removal: {e}")
            display_lcd_message("Error", "Card Removal")
            break

def process_borrow_return(student_id, student_name):
    """Proses peminjaman atau pengembalian buku."""
    try:
        print("Please scan the book's RFID tag...")
        display_lcd_message(f"Hi {student_name}", "Scan Book ID")
        rfid_code = reader.read()[0]  # Membaca UID buku

        conn = connect_db()
        cursor = conn.cursor()

        # Cek status buku di database
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
                # Tampilkan "Borrow Success" di line 1 dan judul buku di line 2 dengan scrolling
                if len(title) > 16:
                    display_lcd_message("Borrow Success")
                    scroll_text(1, title)  # Scroll judul buku di baris kedua
                else:
                    display_lcd_message("Borrow Success", title)
            elif status == 'dipinjam':
                # Proses pengembalian buku
                return_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE borrowed_books SET return_date = ?
                    WHERE book_id = ? AND student_id = ? AND return_date IS NULL
                ''', (return_date, book_id, student_id))
                cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = ?", (book_id,))
                conn.commit()
                # Tampilkan "Return Success" di line 1 dan judul buku di line 2 dengan scrolling
                if len(title) > 16:
                    display_lcd_message("Return Success")
                    scroll_text(1, title)  # Scroll judul buku di baris kedua
                else:
                    display_lcd_message("Return Success", title)
            else:
                print(f"Error: Unknown book status '{status}'.")
                display_lcd_message("Error", "Invalid Status")
        else:
            print("Error: Book not found.")
            display_lcd_message("Error", "Book Not Found")

        conn.close()

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_lcd_message("Error", "Borrow/Return")

def borrow_return():
    """Fungsi utama untuk proses peminjaman/pengembalian buku."""
    student_rfid = read_rfid_card()
    
    if student_rfid is None:
        print("Error: No card detected.")
        display_lcd_message("Error", "No Card Detected")
        return

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students WHERE rfid_code = ?", (student_rfid,))
    student = cursor.fetchone()
    conn.close()

    if student:
        student_id, student_name = student
        print(f"Student verified: {student_name}")

        wait_until_card_removed()

        process_borrow_return(student_id, student_name)
    else:
        print("Error: Student not found.")
        display_lcd_message("Error", "Student Not Found")

if __name__ == '__main__':
    try:
        while True:  # Loop untuk terus menerima pengguna baru
            borrow_return()
            time.sleep(2)  # Beri jeda waktu sebentar sebelum pengguna berikutnya
    finally:
        GPIO.cleanup()  # Bersihkan GPIO saat program selesai
