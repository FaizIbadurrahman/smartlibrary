from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import get_firestore_db
from RPLCD.i2c import CharLCD

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

def scroll_text(line, text, delay=0.3):
    """Scroll text if it's longer than 16 characters."""
    lcd.cursor_pos = (line, 0)
    if len(text) <= 16:
        lcd.write_string(text)
        return

    lcd.write_string(text[:16])
    time.sleep(delay)

    for i in range(1, len(text) - 15):
        lcd.cursor_pos = (line, 0)
        lcd.write_string(text[i:i + 16])
        time.sleep(delay)

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

        db = get_firestore_db()

        # Fetch book information
        book_ref = db.collection('books').where('rfid_code', '==', rfid_code).limit(1).get()
        if not book_ref:
            display_lcd_message("Error", "Book Not Found")
            return

        book_doc = book_ref[0]
        book_data = book_doc.to_dict()
        book_id, title, status = book_doc.id, book_data['title'], book_data['status']

        if status == 'tersedia':
            # Borrow book
            borrow_date = time.strftime("%Y-%m-%d %H:%M:%S")
            db.collection('borrowed_books').add({
                'student_id': student_id,
                'book_id': book_id,
                'borrow_date': borrow_date,
                'return_date': None
            })
            db.collection('books').document(book_id).update({'status': 'dipinjam'})
            display_lcd_message("Borrow Success")
            scroll_text(1, title)
        elif status == 'dipinjam':
            # Return book
            return_date = time.strftime("%Y-%m-%d %H:%M:%S")
            borrowed_books_ref = db.collection('borrowed_books').where('book_id', '==', book_id).where('student_id', '==', student_id).where('return_date', '==', None).limit(1).get()
            
            if borrowed_books_ref:
                borrowed_book_id = borrowed_books_ref[0].id
                db.collection('borrowed_books').document(borrowed_book_id).update({'return_date': return_date})
                db.collection('books').document(book_id).update({'status': 'tersedia'})
                display_lcd_message("Return Success")
                scroll_text(1, title)
        else:
            display_lcd_message("Error", "Invalid Status")

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

    # Step 2: Look up student in Firestore
    db = get_firestore_db()
    student_ref = db.collection('students').where('rfid_code', '==', student_rfid).limit(1).get()

    if not student_ref:
        display_lcd_message("Error", "Student Not Found")
        return

    student_doc = student_ref[0]
    student_data = student_doc.to_dict()
    student_id, student_name = student_doc.id, student_data['name']

    print(f"Student verified: {student_name}")
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
