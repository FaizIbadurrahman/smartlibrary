from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD
from datetime import datetime, timedelta

# Initialize LCD 16x2 with I2C
lcd = CharLCD('PCF8574', 0x27)
reader = SimpleMFRC522()

def display_message(line1, line2=""):
    """Displays a message on the LCD."""
    lcd.clear()
    lcd.write_string(line1.center(16))
    if line2:
        lcd.crlf()
        lcd.write_string(line2.center(16))

def read_student_card():
    """Reads the student's RFID card and returns the RFID code."""
    print("Scan student RFID card")
    display_message("Scan Student ID")
    student_rfid, _ = reader.read()
    student_rfid = str(student_rfid).strip()  # Ensure RFID is a string and trimmed
    print(f"DEBUG: Scanned RFID: '{student_rfid}'")  # Debug output
    return student_rfid

def process_borrow_return(student_id, student_name):
    """Processes borrowing or returning of a book."""
    try:
        display_message(f"Hi {student_name}", "Scan Book ID")
        book_rfid, _ = reader.read()
        book_rfid = str(book_rfid).strip()  # Ensure RFID is a string and trimmed
        print(f"DEBUG: Scanned Book RFID: '{book_rfid}'")  # Debug output

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT judul, isbn, gambar, status FROM buku WHERE rfid = %s", (book_rfid,))
            book = cursor.fetchone()

            if book:
                title, isbn, image, status = book
                if status == 'tersedia':
                    # Borrow book
                    return_date = datetime.now() + timedelta(weeks=2)
                    cursor.execute("""
                        INSERT INTO buku_pinjam (judul, isbn, rfid_siswa, rfid_buku, nama, tanggal_kembali, gambar, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'dipinjam')
                    """, (title, isbn, student_id, book_rfid, student_name, return_date, image))
                    cursor.execute("UPDATE buku SET status = 'dipinjam' WHERE rfid = %s", (book_rfid,))
                    conn.commit()
                    display_message("Borrow Success", title[:16])
                elif status == 'dipinjam':
                    # Return book
                    cursor.execute("""
                        UPDATE buku_pinjam
                        SET status = 'sudah dikembalikan', tanggal_kembali = NOW()
                        WHERE rfid_buku = %s AND rfid_siswa = %s AND status = 'dipinjam'
                    """, (book_rfid, student_id))
                    cursor.execute("UPDATE buku SET status = 'tersedia' WHERE rfid = %s", (book_rfid,))
                    conn.commit()
                    display_message("Return Success", title[:16])
                else:
                    display_message("Error", "Invalid Status")
            else:
                display_message("Error", "Book Not Found")

            cursor.close()
            conn.close()
        else:
            display_message("Error", "Database Unavailable")

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_message("Error", "Borrow/Return")
    finally:
        GPIO.cleanup()

def borrow_return():
    """Main function to handle the borrow/return process."""
    student_rfid = read_student_card()
    
    conn = connect_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT rfid, nama FROM siswa WHERE rfid = %s", (student_rfid,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if student:
            student_id, student_name = student
            display_message("Student Verified", student_name)
            time.sleep(2)
            process_borrow_return(student_id, student_name)
        else:
            display_message("Error", "Student Not Found")
    else:
        display_message("Error", "Database Unavailable")

if __name__ == '__main__':
    try:
        while True:  # Continuous loop to handle new users
            borrow_return()
            time.sleep(2)
    finally:
        GPIO.cleanup()
