from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
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

def register_student():
    """Register a new student by reading RFID card."""
    try:
        print("Please scan your RFID card to register a new student.")
        display_lcd_message("Scan Student ID")

        # Read RFID for student card
        student_rfid, text = reader.read()

        # Prompt for student's name
        student_name = input("Enter student name: ")
        print(f"Registering student: {student_name}")
        display_lcd_message("Registering", "Student...")

        # Add student to MySQL
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (rfid_code, name) VALUES (%s, %s)", (student_rfid, student_name))
        conn.commit()
        conn.close()

        print(f"Student {student_name} registered successfully.")
        display_lcd_message("Student Registered", student_name[:16])

    except Exception as e:
        print(f"Error registering student: {e}")
        display_lcd_message("Error", "Registration Failed")

def register_book():
    """Register a new book by reading RFID tag."""
    try:
        print("Please scan the book's RFID tag to register a new book.")
        display_lcd_message("Scan Book RFID")

        # Read RFID for book
        book_rfid, text = reader.read()

        # Prompt for book details
        book_title = input("Enter book title: ")
        book_author = input("Enter book author: ")

        print(f"Registering book: {book_title}")
        display_lcd_message("Registering", "Book...")

        # Add book to MySQL
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (rfid_code, title, author, status) VALUES (%s, %s, %s, 'tersedia')", 
                       (book_rfid, book_title, book_author))
        conn.commit()
        conn.close()

        print(f"Book '{book_title}' by {book_author} registered successfully.")
        
        # Scroll title if longer than 16 characters
        if len(book_title) > 16:
            display_lcd_message("Book Registered", book_title[:16])

    except Exception as e:
        print(f"Error registering book: {e}")
        display_lcd_message("Error", "Registration Failed")
    
def main():
    """Main function to select registration mode."""
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

            time.sleep(2)  # Pause before returning to main menu

    finally:
        GPIO.cleanup()  # Clean up GPIO pins after program ends

if __name__ == '__main__':
    main()
