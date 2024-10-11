from mfrc522 import SimpleMFRC522
from datetime import datetime
import RPi.GPIO as GPIO
from utils import connect_db

# Function to authenticate the student using RFID
def authenticate_student():
    reader = SimpleMFRC522()

    try:
        print("Please scan the student's RFID card...")
        rfid_code = reader.read()[0]  # Read UID from the RFID card

        # Get the student details from the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM students WHERE rfid_code = ?", (rfid_code,))
        student = cursor.fetchone()
        conn.close()

        if student:
            print(f"Student authenticated: {student[1]}")
            return student[0]  # Return the student ID
        else:
            print("Error: Student not found.")
            return None

    finally:
        GPIO.cleanup()

# Function to process book borrowing or returning
def process_book(student_id):
    reader = SimpleMFRC522()

    try:
        print("Please scan the book's RFID tag...")
        rfid_code = reader.read()[0]  # Read UID from the RFID tag

        # Get the book details from the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, status FROM books WHERE rfid_code = ?", (rfid_code,))
        book = cursor.fetchone()

        if book:
            book_id, title, status = book

            if status == 'available':
                # Process book borrowing
                borrow_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO borrowed_books (student_id, book_id, borrow_date)
                    VALUES (?, ?, ?)
                ''', (student_id, book_id, borrow_date))

                cursor.execute("UPDATE books SET status = 'borrowed' WHERE id = ?", (book_id,))
                print(f"Book '{title}' successfully borrowed by student with ID {student_id}.")
            
            else:
                # Process book returning
                return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    UPDATE borrowed_books
                    SET return_date = ?
                    WHERE book_id = ? AND student_id = ? AND return_date IS NULL
                ''', (return_date, book_id, student_id))

                cursor.execute("UPDATE books SET status = 'available' WHERE id = ?", (book_id,))
                print(f"Book '{title}' successfully returned by student with ID {student_id}.")
        
        else:
            print("Error: Book not found.")

        conn.commit()
        conn.close()

    finally:
        GPIO.cleanup()

# Main function for borrowing/returning books
def main():
    while True:
        print("\n1. Borrow or Return a Book")
        print("2. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            student_id = authenticate_student()
            if student_id:
                process_book(student_id)
        elif choice == '2':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == '__main__':
    main()
