import mysql.connector

def connect_db():
    """Establish a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host="srv1094.hstgr.io",
            user="u268211096_siswa",
            password="AlcentSiswa@4848",
            database="u268211096_siswa"  # Replace with the correct database name if different
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def change_column_to_varchar():
    """Change rfid_siswa and rfid_buku columns in buku_pinjam to VARCHAR."""
    conn = None
    cursor = None
    try:
        # Connect to the database
        conn = connect_db()
        if conn is None:
            print("Database connection failed.")
            return
        print("Database connection established.")

        cursor = conn.cursor()

        # SQL commands to modify the column types
        alter_rfid_siswa = "ALTER TABLE buku_pinjam MODIFY COLUMN rfid_siswa VARCHAR(255);"
        alter_rfid_buku = "ALTER TABLE buku_pinjam MODIFY COLUMN rfid_buku VARCHAR(255);"

        # Execute the SQL commands
        print("Changing rfid_siswa column to VARCHAR(255)...")
        cursor.execute(alter_rfid_siswa)
        print("Changing rfid_buku column to VARCHAR(255)...")
        cursor.execute(alter_rfid_buku)

        # Commit the changes
        conn.commit()
        print("Column types successfully updated to VARCHAR(255).")

    except mysql.connector.Error as e:
        print(f"Error altering table: {e}")
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
            print("Cursor closed.")
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    change_column_to_varchar()
