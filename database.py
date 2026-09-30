"""
====================================================================
AI-Based Fake Identity & Document Screening System
Database Management Module (SQLite)
Cybersecurity best practice: Parameterized queries to prevent SQLi
====================================================================
"""

import sqlite3
import os
import shutil
from werkzeug.security import generate_password_hash, check_password_hash

IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

if IS_VERCEL:
    DB_PATH = os.path.join('/tmp', 'database.db')
    orig_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    if not os.path.exists(DB_PATH) and os.path.exists(orig_db):
        try:
            shutil.copyfile(orig_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def get_db_connection():
    """Returns a SQLite connection with Row factory for dict-like access."""
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database tables and populates synthetic test data."""
    if os.path.dirname(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Users Table (Authentication with secure password hashing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Analyst',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Synthetic Documents Table (Reference database of issued documents)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            document_type TEXT NOT NULL,
            name TEXT NOT NULL,
            date_of_birth TEXT,
            issue_date TEXT,
            expiry_date TEXT,
            status TEXT NOT NULL DEFAULT 'Valid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Verification Records Table (Stores each screening analysis)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verification_code TEXT UNIQUE NOT NULL,
            document_type TEXT NOT NULL,
            document_number TEXT,
            extracted_name TEXT,
            risk_score INTEGER NOT NULL,
            result TEXT NOT NULL,
            reasons_json TEXT,
            checks_json TEXT,
            ocr_data_json TEXT,
            image_analysis_json TEXT,
            fingerprint TEXT NOT NULL,
            fingerprint_status TEXT,
            filename TEXT,
            analyst_user TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Fingerprints Table (Cryptographic SHA-256 hash tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_value TEXT NOT NULL,
            document_number TEXT,
            filename TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            screening_count INTEGER DEFAULT 1
        )
    ''')

    # Seed Default Analyst Users if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash("admin123")
        analyst_hash = generate_password_hash("analyst123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ("admin", admin_hash, "Security Administrator"))
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ("analyst", analyst_hash, "Forensic Analyst"))

    # Seed Synthetic Documents Registry (Fictional records for screening check)
    cursor.execute("SELECT COUNT(*) FROM documents")
    if cursor.fetchone()[0] == 0:
        sample_records = [
            ("ABC12345", "ID Card", "John Doe", "1995-04-12", "2020-01-10", "2030-12-31", "Valid"),
            ("XYZ67890", "Passport", "Alex Smith", "1992-08-15", "2019-08-20", "2029-08-20", "Valid"),
            ("TEST0001", "ID Card", "Sample User", "1998-11-23", "2018-05-10", "2028-05-10", "Flagged"),
            ("DL998877", "Driving Licence", "Sarah Connor", "1988-02-28", "2013-01-01", "2023-01-01", "Valid"),  # Expired
            ("STU202601", "College ID", "David Warner", "2004-06-14", "2023-08-01", "2027-06-30", "Valid"),
            ("CERT10020", "Certificate", "Emma Watson", "2001-09-19", "2022-12-01", "2032-12-31", "Valid")
        ]
        cursor.executemany('''
            INSERT INTO documents (document_number, document_type, name, date_of_birth, issue_date, expiry_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_records)

    conn.commit()
    conn.close()
    print("SQLite database initialized successfully at:", DB_PATH)


def verify_user(username, password):
    """Verifies user credentials using PBKDF2 password hashing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def lookup_document_in_db(document_number):
    """
    Checks if a document number exists in the synthetic sample database.
    Uses parameterized query to prevent SQL injection.
    """
    if not document_number or document_number == "Not detected":
        return None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE UPPER(document_number) = ?", (document_number.upper(),))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


if __name__ == '__main__':
    init_db()
