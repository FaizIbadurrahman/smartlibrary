import mysql.connector

def connect_db():
    """Connect to the remote MySQL database."""
    try:
        conn = mysql.connector.connect(
            host="srv1094.hstgr.io",
            user="u268211096_siswa",
            password="AlcentSiswa@4848",
            database="elice"  # Replace with the correct database name if different
        )
        print("Connected to MySQL Database")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
