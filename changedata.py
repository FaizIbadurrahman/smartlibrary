import mysql.connector

def connect_db():
    """Establish a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host="srv1094.hstgr.io",  # Replace with your database host
            user="u268211096_siswa",  # Replace with your database username
            password="AlcentSiswa@4848",  # Replace with your database password
            database="library_db"  # Replace with your database name
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def change_rfid_column_to_varchar():
    """Change the data type of the RFID column in the buku table to VARCHAR."""
    try:
        # Connect to the database
        conn = connect_db()
        if conn is None:
            print("Database connection failed.")
            return
        
        cursor = conn.cursor()
        
        # SQL command to change the column data type
        alter_table_sql = "ALTER TABLE buku MODIFY COLUMN rfid VARCHAR(255);"
        print("Executing SQL: ", alter_table_sql)
        
        # Execute the SQL command
        cursor.execute(alter_table_sql)
        conn.commit()
        print("Column type for 'rfid' successfully changed to VARCHAR(255).")

    except mysql.connector.Error as e:
        print(f"Error altering table: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    change_rfid_column_to_varchar()
