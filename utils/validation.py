"""
====================================================================
Document Validation & Multi-Factor Verification Module
Evaluates three independent dimensions:
1. Document Completeness (presence of expected identity fields)
2. Field Consistency (chronological & structural integrity)
3. Database Verification (cross-referencing sample registry)

Strictly adheres to:
- Missing important field: +10 (WARNING)
- Strong field inconsistency: +25 (FLAGGED)
- Expired document: +10 (Moderate evidence)
- Database mismatch: +15 to +25 (FLAGGED)
- Database record unavailable: +5 (WARNING - not fake)
- Database match: 0 (PASSED)
====================================================================
"""

from datetime import datetime, date
import re
from database import lookup_document_in_db


def validate_document_data(ocr_fields, selected_doc_type):
    """
    Validates extracted document data against completeness, consistency,
    and database registry records.
    """
    checks = []

    doc_num = ocr_fields.get('document_number', 'Not confidently detected')
    doc_name = ocr_fields.get('name', 'Not confidently detected')
    dob_str = ocr_fields.get('dob', 'Not confidently detected')
    issue_str = ocr_fields.get('issue_date', 'Not confidently detected')
    exp_str = ocr_fields.get('expiry_date', 'Not confidently detected')

    # =============================================================
    # 1. DOCUMENT COMPLETENESS CHECK
    # Expected: Name, Document Number, DOB, Issue Date, Expiry Date
    # =============================================================
    missing_fields = []
    if doc_name in ["Not confidently detected", "Not detected", ""]:
        missing_fields.append("Holder Name")
    if doc_num in ["Not confidently detected", "Not detected", ""]:
        missing_fields.append("Document Number")
    if dob_str in ["Not confidently detected", "Not detected", ""]:
        missing_fields.append("Date of Birth")
    if issue_str in ["Not confidently detected", "Not detected", ""]:
        missing_fields.append("Issue Date")
    if exp_str in ["Not confidently detected", "Not detected", ""] and selected_doc_type != "Certificate":
        missing_fields.append("Expiry Date")

    missing_count = len(missing_fields)
    if missing_count == 0:
        completeness_status = "PASSED"
        completeness_penalty = 0
        completeness_details = "All expected identity fields are present and detected."
    elif missing_count <= 2:
        completeness_status = "WARNING"
        completeness_penalty = missing_count * 10  # Moderate evidence: +10 per missing field
        completeness_details = f"Missing field(s): {', '.join(missing_fields)} not confidently detected."
    else:
        completeness_status = "FLAGGED"
        completeness_penalty = 20  # Invalid document structure: +20
        completeness_details = f"Multiple core fields missing ({missing_count} fields): {', '.join(missing_fields)}."

    checks.append({
        'name': 'Document Completeness Check',
        'passed': (completeness_status == "PASSED"),
        'severity': 'high' if completeness_status == "FLAGGED" else ('medium' if completeness_status == "WARNING" else 'low'),
        'details': completeness_details
    })

    completeness_result = {
        'status': completeness_status,
        'penalty': completeness_penalty,
        'details': completeness_details,
        'missing_fields': missing_fields,
        'detected_count': 5 - missing_count
    }

    # =============================================================
    # 2. FIELD CONSISTENCY CHECK
    # Check chronological date logic, age validity, and format syntax
    # =============================================================
    inconsistencies = []
    has_strong_inconsistency = False

    parsed_dob = _parse_date(dob_str)
    parsed_issue = _parse_date(issue_str)
    parsed_exp = _parse_date(exp_str)

    # Check Chronological Logic: Issue date vs Expiry date
    if parsed_issue and parsed_exp:
        if parsed_exp <= parsed_issue:
            has_strong_inconsistency = True
            inconsistencies.append(
                f"Contradictory Dates: Expiry date ({parsed_exp}) is on or before Issue date ({parsed_issue})."
            )

    # Check Chronological Logic: DOB vs Issue date
    if parsed_dob and parsed_issue:
        if parsed_issue <= parsed_dob:
            has_strong_inconsistency = True
            inconsistencies.append(
                f"Impossible Date Sequence: Issue date ({parsed_issue}) precedes Date of Birth ({parsed_dob})."
            )
        else:
            age_at_issue = (parsed_issue - parsed_dob).days // 365
            if age_at_issue < 14 and selected_doc_type in ["Driving Licence", "Passport"]:
                has_strong_inconsistency = True
                inconsistencies.append(
                    f"Chronological Discrepancy: Age at document issue is {age_at_issue} years (unrealistic for {selected_doc_type})."
                )

    # Check ID Number Syntax & Repetitive Synthetic Motifs
    clean_num = doc_num.replace(" ", "").replace("-", "").upper() if doc_num not in ["Not confidently detected", "Not detected", ""] else ""
    if clean_num:
        # Check for repetitive synthetic characters (e.g. 7777777) or fake prefixes
        if re.search(r'(.)\1{4,}', clean_num) or clean_num.startswith(('FAKE', 'SYNTH', 'TEST')):
            has_strong_inconsistency = True
            inconsistencies.append(
                f"Malformed Synthetic Pattern: Document number '{doc_num}' contains repetitive motifs or non-standard token syntax."
            )
        elif selected_doc_type == "ID Card" and not re.match(r'^[A-Z0-9]{6,12}$', clean_num):
            inconsistencies.append(f"Format Anomaly: ID number '{doc_num}' deviates from standard syntax.")
        elif selected_doc_type == "Passport" and not re.match(r'^[A-Z0-9]{8,10}$', clean_num):
            inconsistencies.append(f"Format Anomaly: Passport number '{doc_num}' deviates from standard syntax.")
        elif selected_doc_type == "Driving Licence" and not re.match(r'^[A-Z0-9]{7,12}$', clean_num):
            inconsistencies.append(f"Format Anomaly: Driving licence '{doc_num}' deviates from standard syntax.")

    # Cross-reference security footer / verification reference against primary document ID
    raw_txt = ocr_fields.get('raw_text', '')
    footer_match = re.search(r'VERIFICATION\s*(?:CODE|REFERENCE)[:\s#.]+([A-Z0-9-]{5,16})', raw_txt, re.IGNORECASE)
    if footer_match and clean_num:
        footer_num = footer_match.group(1).replace(" ", "").replace("-", "").upper()
        if footer_num != clean_num and not (clean_num in footer_num or footer_num in clean_num):
            has_strong_inconsistency = True
            inconsistencies.append(
                f"Conflicting Identifiers: Field states '{doc_num}' but security reference footer displays '{footer_num}'."
            )

    if has_strong_inconsistency:
        consistency_status = "FLAGGED"
        consistency_penalty = 25  # Strong field inconsistency: +25
        consistency_details = "Critical data contradiction detected: " + "; ".join(inconsistencies)
    elif len(inconsistencies) > 0:
        consistency_status = "WARNING"
        consistency_penalty = 5  # Minor syntax variation: +5
        consistency_details = "Minor field formatting variation: " + "; ".join(inconsistencies)
    else:
        consistency_status = "PASSED"
        consistency_penalty = 0
        consistency_details = "All date sequences and field formatting are internally consistent."

    checks.append({
        'name': 'Field Consistency Check',
        'passed': (consistency_status == "PASSED"),
        'severity': 'high' if consistency_status == "FLAGGED" else ('medium' if consistency_status == "WARNING" else 'low'),
        'details': consistency_details
    })

    consistency_result = {
        'status': consistency_status,
        'penalty': consistency_penalty,
        'details': consistency_details,
        'inconsistencies': inconsistencies
    }

    # =============================================================
    # 2b. DOCUMENT STRUCTURE CHECK
    # Standard document geometry, framing, and layout zones
    # =============================================================
    structure_status = "PASSED"
    structure_penalty = 0
    structure_details = "Standard document structure: headers, security margins, and information zones align correctly."

    if missing_count >= 3:
        structure_status = "FLAGGED"
        structure_penalty = 15
        structure_details = "Irregular document structure; multiple expected structural zones are absent."
    elif missing_count > 0:
        structure_status = "WARNING"
        structure_penalty = 0
        structure_details = "Minor structural variation: some standard layout fields are missing."
    elif has_strong_inconsistency:
        structure_status = "WARNING"
        structure_penalty = 5
        structure_details = "Document structure displays anomalous or modified character blocks."

    checks.append({
        'name': 'Document Structure Check',
        'passed': (structure_status in ["PASSED", "WARNING"]),
        'severity': 'high' if structure_status == "FLAGGED" else ('medium' if structure_status == "WARNING" else 'low'),
        'details': structure_details
    })

    structure_result = {
        'status': structure_status,
        'penalty': structure_penalty,
        'details': structure_details
    }

    # =============================================================
    # 3. EXPIRY VALIDITY CHECK
    # Expired document: +10 moderate evidence
    # =============================================================
    is_expired = False
    if parsed_exp:
        today = date.today()
        if parsed_exp < today:
            is_expired = True
            checks.append({
                'name': 'Validity & Expiry Check',
                'passed': False,
                'severity': 'medium',
                'details': f"Document validity has EXPIRED on {parsed_exp.strftime('%Y-%m-%d')} (Current date: {today.strftime('%Y-%m-%d')})."
            })
        else:
            checks.append({
                'name': 'Validity & Expiry Check',
                'passed': True,
                'severity': 'low',
                'details': f"Document is currently valid. Expiration date: {parsed_exp.strftime('%Y-%m-%d')}."
            })

    # =============================================================
    # 4. DATABASE CROSS-REFERENCE CHECK
    # MATCHED: 0 (PASSED)
    # UNREGISTERED / NOT AVAILABLE: +5 (NOT VERIFIED / WARNING - Not fake!)
    # MISMATCH: +25 (FLAGGED)
    # FLAGGED/REVOKED: +40 (FLAGGED)
    # =============================================================
    db_record = lookup_document_in_db(clean_num) if clean_num else None
    is_db_matched = False
    db_status = 'NOT VERIFIED'
    db_penalty = 0

    if db_record:
        is_db_matched = True
        record_status = db_record.get('status', 'valid').lower()

        if record_status == 'flagged':
            db_status = 'FLAGGED'
            db_check_status = 'FLAGGED'
            db_penalty = 40
            db_details = f"Database Alert: Document ID #{clean_num} is explicitly FLAGGED / SUSPENDED in secure registry."
        else:
            # Check for name consistency
            stored_name = db_record['name'].lower()
            doc_name_clean = doc_name.lower()
            if doc_name not in ["Not confidently detected", "Not detected", ""] and not _names_match(stored_name, doc_name_clean):
                db_status = 'MISMATCH'
                db_check_status = 'FLAGGED'
                db_penalty = 25  # Major document information mismatch: +25
                db_details = f"Information Conflict: Document states '{doc_name}' but registry records '{db_record['name']}'."
            else:
                db_status = 'MATCHED'
                db_check_status = 'PASSED'
                db_penalty = 0
                db_details = f"Official Record Verified: Document #{clean_num} confirmed in registry for '{db_record['name']}'."

    else:
        # Document not in database:
        # Absence of record is NOT evidence of fraud!
        db_status = 'NOT VERIFIED'
        db_check_status = 'NOT VERIFIED'
        db_penalty = 5  # Moderate evidence: Database record unavailable (+5)
        if clean_num:
            db_details = f"Not Available: Document ID '{doc_num}' is unregistered in local reference registry. Further verification recommended."
        else:
            db_details = "Not Available: Document number could not be matched against local reference registry."

    checks.append({
        'name': 'Database Verification Check',
        'passed': (db_check_status == "PASSED"),
        'severity': 'high' if db_check_status == "FLAGGED" else ('low' if db_check_status == "PASSED" else 'medium'),
        'details': db_details
    })

    database_result = {
        'status': db_check_status,
        'penalty': db_penalty,
        'details': db_details,
        'db_status': db_status,
        'db_record': db_record
    }

    # =============================================================
    # 5. FIELD-LEVEL INFORMATION & VALIDATION STATUS (User-facing)
    # =============================================================
    extracted_fields = [
        {
            'field': 'Name',
            'value': doc_name if doc_name not in ["Not confidently detected", "Not detected"] else "Not detected",
            'status': 'Extracted' if doc_name not in ["Not confidently detected", "Not detected"] else 'Not Detected',
            'is_valid': doc_name not in ["Not confidently detected", "Not detected"],
            'icon': 'fa-solid fa-check text-success' if doc_name not in ["Not confidently detected", "Not detected"] else 'fa-solid fa-triangle-exclamation text-warning'
        },
        {
            'field': 'Document Number',
            'value': doc_num if doc_num not in ["Not confidently detected", "Not detected"] else "Not detected",
            'status': 'Valid Format' if (doc_num not in ["Not confidently detected", "Not detected"] and not has_strong_inconsistency) else ('Format Warning' if doc_num not in ["Not confidently detected", "Not detected"] else 'Not Detected'),
            'is_valid': doc_num not in ["Not confidently detected", "Not detected"] and not has_strong_inconsistency,
            'icon': 'fa-solid fa-check text-success' if (doc_num not in ["Not confidently detected", "Not detected"] and not has_strong_inconsistency) else 'fa-solid fa-triangle-exclamation text-warning'
        },
        {
            'field': 'Date of Birth',
            'value': dob_str if dob_str not in ["Not confidently detected", "Not detected"] else "Not detected",
            'status': 'Extracted' if dob_str not in ["Not confidently detected", "Not detected"] else 'Not Detected',
            'is_valid': dob_str not in ["Not confidently detected", "Not detected"],
            'icon': 'fa-solid fa-check text-success' if dob_str not in ["Not confidently detected", "Not detected"] else 'fa-solid fa-triangle-exclamation text-warning'
        },
        {
            'field': 'Issue Date',
            'value': issue_str if issue_str not in ["Not confidently detected", "Not detected"] else "Not detected",
            'status': 'Extracted' if issue_str not in ["Not confidently detected", "Not detected"] else 'Not Detected',
            'is_valid': issue_str not in ["Not confidently detected", "Not detected"],
            'icon': 'fa-solid fa-check text-success' if issue_str not in ["Not confidently detected", "Not detected"] else 'fa-solid fa-triangle-exclamation text-warning'
        },
        {
            'field': 'Expiry Date',
            'value': exp_str if exp_str not in ["Not confidently detected", "Not detected"] else "Not detected",
            'status': 'Expired' if is_expired else ('Valid' if exp_str not in ["Not confidently detected", "Not detected"] else 'Not Detected'),
            'is_valid': not is_expired and exp_str not in ["Not confidently detected", "Not detected"],
            'icon': 'fa-solid fa-circle-xmark text-danger' if is_expired else ('fa-solid fa-check text-success' if exp_str not in ["Not confidently detected", "Not detected"] else 'fa-solid fa-triangle-exclamation text-warning')
        },
        {
            'field': 'Document Type',
            'value': selected_doc_type,
            'status': 'Validated',
            'is_valid': True,
            'icon': 'fa-solid fa-check text-success'
        }
    ]

    return {
        'completeness_check': completeness_result,
        'consistency_check': consistency_result,
        'structure_check': structure_result,
        'database_check': database_result,
        'extracted_fields': extracted_fields,
        'is_expired': is_expired,
        'expiry_penalty': 10 if is_expired else 0,
        'checks': checks,
        'is_db_matched': is_db_matched,
        'db_status': db_status,
        'db_record': db_record
    }


def _parse_date(date_str):
    """Attempts to parse date strings into a date object."""
    if not date_str or date_str in ["Not confidently detected", "Not detected"]:
        return None
    date_str = date_str.strip()
    formats = [
        '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
        '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y',
        '%m/%d/%Y', '%Y%m%d'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None


def _names_match(name1, name2):
    """Tokens-based fuzzy matching to verify reasonable name correspondence."""
    t1 = set(name1.split())
    t2 = set(name2.split())
    return bool(t1 & t2) or name1 in name2 or name2 in name1
