from mfrc522 import SimpleMFRC522
from utils import create_database, connect_db

# Fungsi untuk mendaftarkan siswa
def register_student():
    reader = SimpleMFRC522()
    
    try:
        print("Silakan scan kartu RFID untuk siswa...")
        rfid_code = reader.read()[0]  # Membaca UID kartu RFID
        name = input("Masukkan nama siswa: ")  # Memasukkan nama siswa
        
        # Menyimpan data siswa di database
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO students (name, rfid_code) 
            VALUES (?, ?)
        ''', (name, rfid_code))
        
        conn.commit()
        conn.close()
        print(f"Siswa {name} berhasil didaftarkan dengan RFID {rfid_code}.")
    
    finally:
        reader.cleanup()

# Fungsi untuk mendaftarkan buku
def register_book():
    reader = SimpleMFRC522()

    try:
        print("Silakan scan stiker RFID untuk buku...")
        rfid_code = reader.read()[0]  # Membaca UID stiker RFID
        title = input("Masukkan judul buku: ")  # Memasukkan judul buku
        author = input("Masukkan nama penulis: ")  # Memasukkan nama penulis
        
        # Menyimpan data buku di database
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO books (title, author, rfid_code) 
            VALUES (?, ?, ?)
        ''', (title, author, rfid_code))
        
        conn.commit()
        conn.close()
        print(f"Buku '{title}' berhasil didaftarkan dengan RFID {rfid_code}.")
    
    finally:
        reader.cleanup()

# Menu utama pendaftaran
def main():
    create_database()  # Membuat database jika belum ada
    
    while True:
        print("\n1. Daftarkan Siswa")
        print("2. Daftarkan Buku")
        print("3. Keluar")
        choice = input("Pilih opsi: ")

        if choice == '1':
            register_student()
        elif choice == '2':
            register_book()
        elif choice == '3':
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == '__main__':
    main()
