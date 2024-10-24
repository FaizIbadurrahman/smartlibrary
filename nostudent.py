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
    """Scrolling text jika panjangnya lebih dari 16 karakter."""
    lcd.clear()
    
    # Jika teks lebih pendek dari atau sama dengan 16 karakter, tampilkan langsung
    if len(text) <= 16:
        lcd.cursor_pos = (line, 0)
        lcd.write_string(text)
        return

    # Scrolling jika teks lebih dari 16 karakter
    # Tampilkan teks pertama (16 karakter pertama) langsung
    lcd.cursor_pos = (line, 0)
    lcd.write_string(text[:16])
    
    # Mulai geser teks setelah menampilkan teks pertama
    time.sleep(delay)
    
    for i in range(1, len(text) - 15):  # Loop untuk scroll
        lcd.cursor_pos = (line, 0)  # Set baris yang akan di-scroll
        lcd.write_string(text[i:i + 16])  # Geser window teks sepanjang 16 karakter
        time.sleep(delay)  # Delay untuk memberikan efek scroll

def read_rfid_book():
    """Membaca RFID dari buku dan mengembalikan UID buku."""
    try:
        print("Awaiting book RFID input...")
        display_lcd_message("Scan Book RFID")
        rfid_code, text = reader.read()  # Baca UID buku
        return rfid_code
    except Exception as e:
        print(f"Error reading RFID: {e}")
        display_lcd_message("Error Reading", "RFID Data")
        return None

def process_borrow_return():
    """Proses peminjaman atau pengembalian buku hanya berdasarkan RFID buku."""
    try:
        # Minta pengguna untuk scan buku
        rfid_code = read_rfid_book()
        if rfid_code is None:
            display_lcd_message("Error", "No Book Detected")
            return

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
                    INSERT INTO borrowed_books (book_id, borrow_date)
                    VALUES (?, ?)
                ''', (book_id, borrow_date))
                cursor.execute("UPDATE books SET status = 'dipinjam' WHERE id = ?", (book_id,))
                conn.commit()
                # Scroll jika judul buku lebih dari 16 karakter
                scroll_text(1, f"Borrowed: {title}")
            elif status == 'dipinjam':
                # Proses pengembalian buku
                return_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE borrowed_books SET return_date = ?
                    WHERE book_id = ? AND return_date IS NULL
                ''', (return_date, book_id))
                cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = ?", (book_id,))
                conn.commit()
                # Scroll jika judul buku lebih dari 16 karakter
                scroll_text(1, f"Returned: {title}")
            else:
                display_lcd_message("Error", "Invalid Status")
        else:
            display_lcd_message("Error", "Book Not Found")

        conn.close()

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_lcd_message("Error", "Borrow/Return")

if __name__ == '__main__':
    try:
        while True:  # Loop untuk terus mendeteksi RFID buku
            process_borrow_return()
            time.sleep(2)  # Beri jeda waktu sebentar sebelum mendeteksi buku berikutnya
    finally:
        GPIO.cleanup()  # Bersihkan GPIO saat program selesai
