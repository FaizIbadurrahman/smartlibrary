from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
from utils import connect_db
from RPLCD.i2c import CharLCD

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

def read_rfid():
    """Reads the RFID card and returns the RFID code."""
    while True:
        try:
            print("Waiting for RFID scan...")
            display_message("Scan RFID Card")
            rfid_code, _ = reader.read()  # Blocking read
            rfid_code = str(rfid_code).strip()  # Ensure the RFID is a string and trimmed
            print(f"DEBUG: Scanned RFID: '{rfid_code}'")  # Debugging log
            return rfid_code
        except Exception as e:
            print(f"Error reading RFID: {e}")
            display_message("Error", "Try Again")
            time.sleep(2)

def register_student():
    """Registers a new student by scanning their RFID card."""
    try:
        # Scan RFID
        student_rfid = read_rfid()

        # Input student details
        student_name = input("Enter student name: ")
        student_class = input("Enter student class: ")
        print(f"DEBUG: Registering student: {student_name} with RFID: {student_rfid}")
        display_message("Registering", "Student...")

        # Insert student data into MySQL database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO siswa (rfid, nama, kelas) VALUES (%s, %s, %s)", 
                           (student_rfid, student_name, student_class))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Student {student_name} registered successfully.")
            display_message("Student Registered", student_name[:16])
        else:
            display_message("Error", "Database Unavailable")

    except Exception as e:
        print(f"Error registering student: {e}")
        display_message("Error", "Registration Failed")

def register_book():
    """Registers a new book by scanning its RFID tag."""
    try:
        # Scan RFID
        book_rfid = read_rfid()  # Reuse the read_rfid function for consistent handling

        # Input book details
        book_isbn = input("Enter book ISBN: ")
        book_title = input("Enter book title: ")
        book_synopsis = input("Enter book synopsis: ")
        book_image = input("Enter image URL (optional, press Enter to skip): ")

        # Validate that the user provided essential inputs
        if not book_isbn or not book_title:
            print("ERROR: ISBN and Title are required.")
            display_message("Error", "ISBN/Title Missing")
            return

        print(f"DEBUG: Registering book: '{book_title}' with RFID: '{book_rfid}'")
        display_message("Registering", "Book...")

        # Insert book data into MySQL database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO buku (rfid, isbn, judul, sinopsis, gambar, status) 
                VALUES (%s, %s, %s, %s, %s, 'tersedia')
            """, (book_rfid, book_isbn, book_title, book_synopsis, book_image))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Book '{book_title}' registered successfully.")
            display_message("Book Registered", book_title[:16])
        else:
            display_message("Error", "Database Unavailable")

    except Exception as e:
        print(f"Error registering book: {e}")
        display_message("Error", "Registration Failed")


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
                display_message("Invalid", "Choice")

            time.sleep(2)  # Pause before returning to the main menu

    finally:
        GPIO.cleanup()  # Clean up GPIO pins after program ends

if __name__ == '__main__':
    main()
