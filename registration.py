from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
from utils import create_database, connect_db

# Function to check if an RFID code exists in the students table
def rfid_exists_in_students(rfid_code):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE rfid_code = ?', (rfid_code,))
    student = cursor.fetchone()
    conn.close()
    return student is not None

# Function to check if an RFID code exists in the books table
def rfid_exists_in_books(rfid_code):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books WHERE rfid_code = ?', (rfid_code,))
    book = cursor.fetchone()
    conn.close()
    return book is not None

# Function to register a student
def register_student():
    reader = SimpleMFRC522()

    try:
        print("Please scan the RFID card for the student...")
        rfid_code = reader.read()[0]  # Read UID from the RFID card
        name = input("Enter the student's name: ")

        # Check if RFID code already exists in students
        if rfid_exists_in_students(rfid_code):
            print(f"Error: RFID code {rfid_code} is already registered for a student.")
            return

        # Save student data in the database
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO students (name, rfid_code) 
            VALUES (?, ?)
        ''', (name, rfid_code))
        
        conn.commit()
        conn.close()
        print(f"Student '{name}' registered successfully with RFID {rfid_code}.")
    
    finally:
        GPIO.cleanup()  # Ensure GPIO resources are released properly

# Function to register a book
def register_book():
    reader = SimpleMFRC522()

    try:
        print("Please scan the RFID tag for the book...")
        rfid_code = reader.read()[0]  # Read UID from the RFID tag
        title = input("Enter the book title: ")  # Enter the book title
        author = input("Enter the author's name: ")  # Enter the author's name

        # Check if RFID code already exists in books
        if rfid_exists_in_books(rfid_code):
            print(f"Error: RFID code {rfid_code} is already registered for a book.")
            return

        # Save book data in the database
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books (title, author, rfid_code) 
            VALUES (?, ?, ?)
        ''', (title, author, rfid_code))
        
        conn.commit()
        conn.close()
        print(f"Book '{title}' by {author} registered successfully with RFID {rfid_code}.")
    
    finally:
        GPIO.cleanup()  # Ensure GPIO resources are released properly

# Main function to handle user input
def main():
    create_database()  # Ensure the database and tables are created
    
    while True:
        print("\n1. Register Student")
        print("2. Register Book")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            register_student()
        elif choice == '2':
            register_book()
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == '__main__':
    main()
