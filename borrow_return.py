from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD

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
    return student_rfid

def process_borrow_return(student_id, student_name):
    """Processes borrowing or returning of a book."""
    try:
        display_message(f"Hi {student_name}", "Scan Book ID")
        book_rfid, _ = reader.read()

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, isbn, title, sinopsis, status FROM books WHERE rfid_code = %s", (book_rfid,))
            book = cursor.fetchone()

            if book:
                book_id, isbn, title, synopsis, status = book
                if status == 'tersedia':
                    # Borrow book
                    cursor.execute("INSERT INTO borrowed_books (student_id, book_id, borrow_date) VALUES (%s, %s, NOW())", 
                                   (student_id, book_id))
                    cursor.execute("UPDATE books SET status = 'dipinjam' WHERE id = %s", (book_id,))
                    conn.commit()
                    display_message("Borrow Success", title[:16])
                elif status == 'dipinjam':
                    # Return book
                    cursor.execute("UPDATE borrowed_books SET return_date = NOW() WHERE book_id = %s AND student_id = %s AND return_date IS NULL", 
                                   (book_id, student_id))
                    cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = %s", (book_id,))
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
        cursor.execute("SELECT id, nama FROM students WHERE rfid_code = %s", (student_rfid,))
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
