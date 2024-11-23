from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD
from datetime import datetime, timedelta

# Initialize LCD 16x2 with I2C (address may vary, e.g., 0x27)
lcd = CharLCD('PCF8574', 0x27)
reader = SimpleMFRC522()

def display_message(line1, line2=""):
    """Displays a message on the LCD."""
    lcd.clear()
    lcd.write_string(line1.center(16))
    if line2:
        lcd.crlf()
        lcd.write_string(line2.center(16))

def wait_until_card_removed():
    """Waits until the RFID card is removed."""
    print("Waiting for card removal...")
    display_message("Remove Card", "Please Wait")
    
    while True:
        rfid_code, _ = reader.read_no_block()  # Non-blocking read
        if rfid_code is None:
            print("Card removed.")
            display_message("Card Removed", "")
            break
        time.sleep(0.5)  # Short delay to reduce CPU usage

def read_student_card():
    """Reads the student's RFID card and returns the RFID code."""
    print("Scan student RFID card")
    display_message("Scan Student ID")
    student_rfid, _ = reader.read()

    # Convert RFID to string and strip any leading/trailing whitespace
    student_rfid = str(student_rfid).strip()
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
            # Fetch book details
            cursor.execute("SELECT judul, isbn, gambar, status FROM buku WHERE rfid = %s", (book_rfid,))
            book = cursor.fetchone()

            if book:
                title, isbn, image, status = book
                if status == 'tersedia':
                    # Borrow book
                    return_date = datetime.now() + timedelta(days=7)  # Set return date to current date + 7 days
                    cursor.execute("""
                        INSERT INTO buku_pinjam (judul, isbn, rfid_siswa, rfid_buku, nama, tanggal_kembali, gambar, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'dipinjam')
                    """, (title, isbn, student_id, book_rfid, student_name, return_date, image))
                    cursor.execute("UPDATE buku SET status = 'dipinjam' WHERE rfid = %s", (book_rfid,))
                    conn.commit()
                    print(f"Book '{title}' borrowed successfully.")
                    display_message("Borrow Success", title[:16])

                elif status == 'dipinjam':
                    # Return book
                    cursor.execute("""
                        DELETE FROM buku_pinjam
                        WHERE rfid_buku = %s AND rfid_siswa = %s AND status = 'dipinjam'
                    """, (book_rfid, student_id))
                    cursor.execute("UPDATE buku SET status = 'tersedia' WHERE rfid = %s", (book_rfid,))
                    conn.commit()
                    print(f"Book '{title}' returned successfully.")
                    display_message("Return Success", title[:16])
                else:
                    print(f"Error: Unknown book status '{status}'.")
                    display_message("Error", "Invalid Status")
            else:
                print("Error: Book not found.")
                display_message("Error", "Book Not Found")

            cursor.close()
            conn.close()
        else:
            display_message("Error", "Database Unavailable")

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_message("Error", "Borrow/Return")


def borrow_return():
    """Main function to handle the borrow/return process."""
    conn = connect_db()
    student_rfid = read_student_card()

    # Print the RFID being scanned
    print(f"DEBUG: Scanned student RFID: '{student_rfid}'")

    # Strip any extra spaces or characters from the RFID value
    student_rfid = str(student_rfid).strip()
    print(f"DEBUG: Cleaned student RFID: '{student_rfid}'")  # Print cleaned RFID

    # Wait for card removal
    wait_until_card_removed()

    if conn:
        cursor = conn.cursor()

        # Print the RFID being sent to the query
        print(f"DEBUG: Querying student with RFID: '{student_rfid}'")
        cursor.execute("SELECT rfid, nama FROM siswa WHERE rfid = %s", (student_rfid,))
        student = cursor.fetchone()

        # Debug: check if student is fetched or not
        if student:
            print(f"DEBUG: Student found: {student}")
        else:
            print(f"DEBUG: No student found for RFID: '{student_rfid}'")  # Detailed debug message

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
            time.sleep(2)  # Allow a short delay before processing the next user
    finally:
        GPIO.cleanup()
