import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase app
cred = credentials.Certificate('/path/to/firebase-adminsdk.json')  # Replace with the path to your Firebase credential JSON file
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

def get_firestore_db():
    """Return the Firestore database client."""
    return db
