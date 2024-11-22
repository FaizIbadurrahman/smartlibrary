import mysql.connector
from utils import connect_db  # Assuming you already have a `connect_db` function

def reset_database():
    """Resets the database by removing all data from specific tables."""
    try:
        conn = connect_db()
        if conn:
            cursor = conn.cursor()

            # List of tables to reset (e.g., siswa, buku)
            tables_to_reset = ['siswa', 'buku', 'buku_pinjam']  # Add any other tables you need to reset

            for table in tables_to_reset:
                # Delete all records from the table
                print(f"Resetting table: {table}")
                cursor.execute(f"DELETE FROM {table}")
                
                # Optionally reset the AUTO_INCREMENT counter for each table
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
                print(f"Table {table} reset successfully.")
            
            conn.commit()  # Commit changes
            cursor.close()
            conn.close()

            print("Database reset completed.")
        else:
            print("Database connection failed.")

    except mysql.connector.Error as err:
        print(f"Error resetting database: {err}")

if __name__ == '__main__':
    reset_database()
