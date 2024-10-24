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

def register_student():
    """Registrasi siswa baru dengan membaca RFID kartu."""
    try:
        print("Please scan your RFID card to register a new student.")
        display_lcd_message("Scan Student ID")

        # Baca kartu RFID siswa
        student_rfid, text = reader.read()

        student_name = input("Enter student name: ")
        print(f"Registering student: {student_name}")
        display_lcd_message("Registering", "Student...")

        # Masukkan data siswa ke database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (rfid_code, name) VALUES (?, ?)", (student_rfid, student_name))
        conn.commit()
        conn.close()

        print(f"Student {student_name} registered successfully.")
        display_lcd_message("Student Registered", student_name[:16])

    except Exception as e:
        print(f"Error registering student: {e}")
        display_lcd_message("Error", "Registration Failed")
    
def register_book():
    """Registrasi buku baru dengan membaca RFID tag buku."""
    try:
        print("Please scan the book's RFID tag to register a new book.")
        display_lcd_message("Scan Book RFID")

        # Baca RFID buku
        book_rfid, text = reader.read()

        book_title = input("Enter book title: ")
        book_author = input("Enter book author: ")

        print(f"Registering book: {book_title}")
        display_lcd_message("Registering", "Book...")

        # Masukkan data buku ke database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (rfid_code, title, author, status) VALUES (?, ?, ?, 'tersedia')", 
                       (book_rfid, book_title, book_author))
        conn.commit()
        conn.close()

        print(f"Book '{book_title}' by {book_author} registered successfully.")
        
        # Jika judul lebih dari 16 karakter, lakukan scrolling
        if len(book_title) > 16:
            scroll_text(1, f"Book: {book_title}")
        else:
            display_lcd_message("Book Registered", book_title[:16])

    except Exception as e:
        print(f"Error registering book: {e}")
        display_lcd_message("Error", "Registration Failed")
    
def main():
    """Fungsi utama untuk memilih mode registrasi."""
    try:
        while True:
            print("\n1. Register Student")
            print("2. Register Book")
            choice = input("Choose an option (1 or 2): ")

            if choice == '1':
                register_student()
            elif choice == '2':
                register_book()
            else:
                print("Invalid choice. Please enter 1 or 2.")
                display_lcd_message("Invalid", "Choice")

            time.sleep(2)  # Jeda waktu sebelum kembali ke menu utama

    finally:
        GPIO.cleanup()  # Bersihkan GPIO saat program selesai

if __name__ == '__main__':
    main()
