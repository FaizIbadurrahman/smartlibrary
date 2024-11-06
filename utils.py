import mysql.connector

def connect_db():
    """Connect to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host="localhost",  # MySQL server host
            user="root",  # MySQL username
            password="",  # MySQL password
            database="library_db"  # The database you want to connect to
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
