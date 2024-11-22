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

def register_student():
    """Registers a new student by scanning their RFID card."""
    try:
        print("Scan the student RFID card")
        display_message("Scan Student ID")
        student_rfid, _ = reader.read()

        # Convert RFID to string and strip any leading/trailing whitespace
        student_rfid = str(student_rfid).strip()
        print(f"DEBUG: Scanned student RFID: {student_rfid}")  # Debugging the scanned RFID

        student_name = input("Enter student name: ")
        student_class = input("Enter student class: ")
        print(f"Registering student: {student_name}")
        display_message("Registering", "Student...")

        # Insert student data into MySQL database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO siswa (rfid, nama, kelas) VALUES (%s, %s, %s)", (student_rfid, student_name, student_class))
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
    finally:
        GPIO.cleanup()

def display_message(line1, line2=""):
    """Displays a message on the LCD."""
    lcd.clear()
    lcd.write_string(line1.center(16))
    if line2:
        lcd.crlf()
        lcd.write_string(line2.center(16))

def register_student():
    """Registers a new student by scanning their RFID card."""
    try:
        print("Scan the student RFID card")
        display_message("Scan Student ID")
        student_rfid, _ = reader.read()
        
        # Ensure RFID is treated as a string and strip any unwanted whitespace
        student_rfid = str(student_rfid).strip()

        # Check if the RFID is empty
        if len(student_rfid) == 0:
            print("Invalid RFID.")
            display_message("Invalid RFID", "Try Again.")
            return

        # Ask for the student name and class
        student_name = input("Enter student name: ")
        student_class = input("Enter student class: ")
        print(f"Registering student: {student_name}")
        display_message("Registering", "Student...")

        # Insert student data into MySQL database
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            
            # Insert into the 'siswa' table with 'rfid' as a VARCHAR
            cursor.execute("INSERT INTO siswa (rfid, nama, kelas) VALUES (%s, %s, %s)", (student_rfid, student_name, student_class))
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
    finally:
        GPIO.cleanup()

def main():
    """Main function to run the student registration."""
    try:
        register_student()
    finally:
        GPIO.cleanup()  # Clean up GPIO pins after program ends

if __name__ == '__main__':
    main()


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
