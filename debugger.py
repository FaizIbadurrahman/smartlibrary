import mysql.connector
from mfrc522 import SimpleMFRC522
from utils import connect_db  # Assuming connect_db function is defined as in your previous code

def check_missing_data():
    """Checks for missing student or book data in the database."""
    conn = connect_db()

    if conn:
        cursor = conn.cursor()

        # Check for students missing from the database
        print("Checking for missing students in the database...")
        cursor.execute("SELECT rfid, nama FROM siswa")
        students_in_db = cursor.fetchall()

        for student in students_in_db:
            rfid_db, name_db = student
            print(f"Student in DB: {rfid_db} | Name: {name_db}")

        # Check for books missing from the database
        print("Checking for missing books in the database...")
        cursor.execute("SELECT rfid, judul FROM buku")
        books_in_db = cursor.fetchall()

        for book in books_in_db:
            rfid_db, title_db = book
            print(f"Book in DB: {rfid_db} | Title: {title_db}")

        cursor.close()
        conn.close()

def check_data_mismatch(rfid_scanned, type_check='student'):
    """Checks for mismatched data by comparing scanned RFID with database entries."""
    conn = connect_db()
    
    if conn:
        cursor = conn.cursor()

        if type_check == 'student':
            # Check if the student exists in the database and if the scanned RFID matches
            cursor.execute("SELECT rfid, nama FROM siswa WHERE rfid = %s", (rfid_scanned,))
            student_in_db = cursor.fetchone()

            if student_in_db:
                rfid_db, name_db = student_in_db
                if rfid_scanned.strip() == rfid_db.strip():  # Compare stripped values
                    print(f"Match found for student: {name_db}")
                else:
                    print(f"Mismatch: Scanned RFID {rfid_scanned} does not match stored {rfid_db}")
            else:
                print(f"Student not found for RFID: {rfid_scanned}")
        
        elif type_check == 'book':
            # Check if the book exists in the database and if the scanned RFID matches
            cursor.execute("SELECT rfid, judul FROM buku WHERE rfid = %s", (rfid_scanned,))
            book_in_db = cursor.fetchone()

            if book_in_db:
                rfid_db, title_db = book_in_db
                if rfid_scanned.strip() == rfid_db.strip():  # Compare stripped values
                    print(f"Match found for book: {title_db}")
                else:
                    print(f"Mismatch: Scanned RFID {rfid_scanned} does not match stored {rfid_db}")
            else:
                print(f"Book not found for RFID: {rfid_scanned}")
        
        cursor.close()
        conn.close()

def register_student():
    """Registers a new student and checks for data mismatches."""
    try:
        reader = SimpleMFRC522()
        print("Scan the student RFID card")
        student_rfid, _ = reader.read()
        student_rfid = str(student_rfid).strip()  # Strip spaces or extra characters

        # Check for mismatches with database
        check_data_mismatch(student_rfid, type_check='student')

        # Proceed with normal student registration if no mismatch
        student_name = input("Enter student name: ")
        student_class = input("Enter student class: ")
        print(f"Registering student: {student_name}")

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO siswa (rfid, nama, kelas) VALUES (%s, %s, %s)", 
                           (student_rfid, student_name, student_class))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Student {student_name} registered successfully.")
        else:
            print("Database connection failed.")
    
    except Exception as e:
        print(f"Error: {e}")

def register_book():
    """Registers a new book and checks for data mismatches."""
    try:
        reader = SimpleMFRC522()
        print("Scan the book RFID tag")
        book_rfid, _ = reader.read()
        book_rfid = str(book_rfid).strip()  # Strip spaces or extra characters

        # Check for mismatches with database
        check_data_mismatch(book_rfid, type_check='book')

        # Proceed with normal book registration if no mismatch
        book_isbn = input("Enter book ISBN: ")
        book_title = input("Enter book title: ")
        book_synopsis = input("Enter book synopsis: ")
        book_image = input("Enter image URL: ")

        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO buku (rfid, isbn, judul, sinopsis, gambar, status) VALUES (%s, %s, %s, %s, %s, 'tersedia')", 
                           (book_rfid, book_isbn, book_title, book_synopsis, book_image))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Book '{book_title}' registered successfully.")
        else:
            print("Database connection failed.")
    
    except Exception as e:
        print(f"Error: {e}")

def borrow_return():
    """Process borrow/return and check for missing or mismatched data."""
    reader = SimpleMFRC522()
    print("Scan student RFID for borrowing/returning a book")
    student_rfid, _ = reader.read()
    student_rfid = str(student_rfid).strip()

    # Check for mismatches with database
    check_data_mismatch(student_rfid, type_check='student')

    # Continue with book borrowing or return process as usual...
    print("Proceeding with book borrowing/returning...")

# Example of checking for missing data
check_missing_data()

# Example of registering a student and checking for data mismatch
register_student()

# Example of borrowing/returning and checking for data mismatch
borrow_return()
