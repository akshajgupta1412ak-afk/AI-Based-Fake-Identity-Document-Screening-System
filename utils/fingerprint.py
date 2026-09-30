"""
====================================================================
Digital Document Fingerprinting Module (SHA-256)
Cybersecurity principle: Cryptographic Integrity Verification
====================================================================
"""

import hashlib
import sqlite3
from database import get_db_connection


def compute_file_sha256(filepath):
    """
    Computes a cryptographic SHA-256 hash digest of a file.
    Reads file in 64KB binary chunks to handle large files safely.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_and_record_fingerprint(hash_value, document_number, filename):
    """
    Checks if the document fingerprint exists in the database.
    Detects if the exact file was previously uploaded, or if the same
    document number was previously registered with a DIFFERENT hash.
    
    Returns:
        dict: {
            'fingerprint': str,
            'status': 'NEW_DOCUMENT' | 'IDENTICAL_REUPLOAD' | 'DOCUMENT_CHANGED',
            'message': str,
            'risk_penalty': int
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Check if the exact hash was seen before
    cursor.execute("SELECT * FROM fingerprints WHERE hash_value = ?", (hash_value,))
    exact_match = cursor.fetchone()

    # 2. Check if this document number was seen with another hash
    diff_hash_match = None
    if document_number and document_number != "Not detected":
        cursor.execute(
            "SELECT * FROM fingerprints WHERE UPPER(document_number) = ? AND hash_value != ?",
            (document_number.upper(), hash_value)
        )
        diff_hash_match = cursor.fetchone()

    status = 'NEW_DOCUMENT'
    message = 'First time this document file has been screened.'
    risk_penalty = 0

    if diff_hash_match:
        # Crucial requirement: "If the fingerprint is different, display:
        # 'Document has changed since previous verification.'"
        status = 'DOCUMENT_CHANGED'
        message = 'Document has changed since previous verification (hash mismatch for same Document ID).'
        risk_penalty = 35
    elif exact_match:
        status = 'IDENTICAL_REUPLOAD'
        message = f'Exact file previously screened on {exact_match["first_seen"]} (Identical SHA-256 digest).'
        risk_penalty = 5
        # Update count
        cursor.execute(
            "UPDATE fingerprints SET screening_count = screening_count + 1 WHERE id = ?",
            (exact_match['id'],)
        )
        conn.commit()
    else:
        # Record new fingerprint
        cursor.execute(
            "INSERT INTO fingerprints (hash_value, document_number, filename) VALUES (?, ?, ?)",
            (hash_value, document_number if document_number != "Not detected" else None, filename)
        )
        conn.commit()

    conn.close()

    return {
        'fingerprint': hash_value,
        'status': status,
        'message': message,
        'risk_penalty': risk_penalty
    }
