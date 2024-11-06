from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD
import os

os.chdir('/home/bomi/smartlibrary')

# Initialize LCD 16x2 with I2C (e.g., 0x27)
lcd = CharLCD('PCF8574', 0x27)

# Initialize RFID Reader
reader = SimpleMFRC522()

def clear_lcd():
    """Clear the LCD display."""
    lcd.clear()

def center_text(text, width=16):
    """Center text for the LCD display."""
    if len(text) < width:
        padding = (width - len(text)) // 2
        return ' ' * padding + text + ' ' * padding
    return text[:width]  # Truncate text if it's longer than 16 characters

def display_lcd_message(line1, line2=""):
    """Display a message on the LCD with centered text."""
    lcd.clear()  # Clear screen
    lcd.write_string(center_text(line1))
    if line2:
        lcd.crlf()  # Move to line 2
        lcd.write_string(center_text(line2))

def read_rfid_card():
    """Read RFID for student card and return UID."""
    try:
        print("Awaiting student RFID input...")
        display_lcd_message("Scan your ID")
        rfid_code, text = reader.read()
        return rfid_code
    except Exception as e:
        print(f"Error reading RFID: {e}")
        display_lcd_message("Error Reading", "Card Data")
        return None

def wait_until_card_removed():
    """Wait until RFID card is removed."""
    print("Please remove the card...")
    display_lcd_message("Please", "Remove Card")
    
    no_card_count = 0
    threshold = 3
    
    while True:
        try:
            rfid_code, text = reader.read_no_block()
            if rfid_code is None:
                no_card_count += 1
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
    """Process borrowing or returning a book."""
    try:
        print("Please scan the book's RFID tag...")
        display_lcd_message(f"Hi {student_name}", "Scan Book ID")
        rfid_code = reader.read()[0]

        conn = connect_db()
        cursor = conn.cursor()

        # Check book availability in MySQL
        cursor.execute("SELECT id, title, status FROM books WHERE rfid_code = %s", (rfid_code,))
        book = cursor.fetchone()

        if book:
            book_id, title, status = book

            if status == 'tersedia':
                # Borrow book
                borrow_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO borrowed_books (student_id, book_id, borrow_date) VALUES (%s, %s, %s)", 
                               (student_id, book_id, borrow_date))
                cursor.execute("UPDATE books SET status = 'dipinjam' WHERE id = %s", (book_id,))
                conn.commit()
                display_lcd_message("Borrow Success", title[:16])
            elif status == 'dipinjam':
                # Return book
                return_date = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE borrowed_books SET return_date = %s WHERE book_id = %s AND student_id = %s AND return_date IS NULL", 
                               (return_date, book_id, student_id))
                cursor.execute("UPDATE books SET status = 'tersedia' WHERE id = %s", (book_id,))
                conn.commit()
                display_lcd_message("Return Success", title[:16])
            else:
                display_lcd_message("Error", "Invalid Status")
        else:
            display_lcd_message("Error", "Book Not Found")

        conn.close()

    except Exception as e:
        print(f"Error during borrow/return process: {e}")
        display_lcd_message("Error", "Borrow/Return")

def borrow_return():
    """Main function to handle borrow/return process."""
    # Step 1: Verify student card
    student_rfid = read_rfid_card()
    
    if student_rfid is None:
        display_lcd_message("Error", "No Card Detected")
        return

    # Step 2: Look up student in MySQL
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM students WHERE rfid_code = %s", (student_rfid,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        display_lcd_message("Error", "Student Not Found")
        return

    student_id, student_name = student
    display_lcd_message("Student Verified", student_name)

    # Step 3: Wait until student card is removed
    wait_until_card_removed()

    # Step 4: Process borrow/return for a book
    process_borrow_return(student_id, student_name)

if __name__ == '__main__':
    try:
        while True:  # Continuous loop to handle new users
            borrow_return()
            time.sleep(2)
    finally:
        GPIO.cleanup()
