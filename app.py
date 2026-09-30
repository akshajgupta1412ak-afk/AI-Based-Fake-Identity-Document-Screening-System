"""
====================================================================
AI-Based Fake Identity & Document Screening System
Modern Document Security & Verification Platform
College Project: 3rd-Semester B.Tech Computer Science (Cybersecurity)
====================================================================
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from werkzeug.utils import secure_filename

# Database and Analysis Modules
from database import init_db, get_db_connection, verify_user
from utils.fingerprint import compute_file_sha256, check_and_record_fingerprint
from utils.ocr import extract_document_fields
from utils.validation import validate_document_data
from utils.image_analysis import screen_image_tampering, check_image_quality
from utils.ai_detection import detect_ai_synthetic_indicators
from utils.risk_score import calculate_risk_score

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cybersec_super_secret_key_demo_v1")

class VercelQueryPathMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        if '__url=' in query_string:
            import urllib.parse
            parsed = urllib.parse.parse_qs(query_string)
            if '__url' in parsed and parsed['__url']:
                real_path = parsed['__url'][0]
                if not real_path.startswith('/'):
                    real_path = '/' + real_path
                environ['PATH_INFO'] = real_path
                clean_params = [p for p in query_string.split('&') if not p.startswith('__url=')]
                environ['QUERY_STRING'] = '&'.join(clean_params)
        elif environ.get('PATH_INFO', '').startswith('/api/index'):
            sub_path = environ['PATH_INFO'].replace('/api/index.py', '').replace('/api/index', '')
            environ['PATH_INFO'] = sub_path or '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelQueryPathMiddleware(app.wsgi_app)

# Vercel Serverless Environment detection & configuration
IS_VERCEL = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))

if IS_VERCEL:
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')

SAMPLE_DOCS_FOLDER = os.path.join(app.root_path, 'sample_docs')
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(SAMPLE_DOCS_FOLDER, exist_ok=True)
except Exception:
    pass

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB upload limit
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}


def is_allowed_file(filename):
    """Validates if an uploaded filename has a safe permitted extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Initialize database schema on startup
init_db()


# ====================================================================
# CORE SCREENING PIPELINE RUNNER
# ====================================================================

def run_screening_pipeline(filepath, document_type, filename, analyst_username='Analyst'):
    """
    Executes the complete document screening pipeline across 6 independent checks:
    1. Cryptographic SHA-256 Fingerprinting
    2. Optical Information Extraction (Windows Media OCR / Tesseract)
    3. Document Completeness, Consistency & Database Validation
    4. OpenCV Visual Tampering Screening
    5. AI / Synthetic Document Indicators
    6. Multi-Factor Risk Assessment Engine (0-100) & Calibrated 3-Tier Classification
    Saves the audit dossier into SQLite and returns the verification code.
    """
    # 1. SHA-256 Cryptographic Fingerprint
    file_hash = compute_file_sha256(filepath)

    # 2. Optical Character Recognition
    ocr_data = extract_document_fields(filepath)
    doc_number = ocr_data.get('document_number', 'Not detected')
    extracted_name = ocr_data.get('name', 'Not detected')

    # Fingerprint check against previous submissions
    fingerprint_res = check_and_record_fingerprint(file_hash, doc_number, filename)

    # 3. Validation against Rules & SQLite Database
    validation_res = validate_document_data(ocr_data, document_type)

    # 4. OpenCV Image Tampering Screening
    image_analysis_res = screen_image_tampering(filepath)

    # 5. AI / Synthetic Document Indicators Screening
    ai_detection_res = detect_ai_synthetic_indicators(filepath, ocr_data)

    # 6. Multi-Factor Risk Score Calculation (6 Independent Checks)
    risk_res = calculate_risk_score(ocr_data, validation_res, image_analysis_res, ai_detection_res, fingerprint_res)

    # 7. Persist Verification Record in SQLite Database
    verification_code = f"VER-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    meta_payload = {
        'reasons': risk_res.get('reasons', []),
        'positive_indicators': risk_res.get('positive_indicators', []),
        'attention_indicators': risk_res.get('attention_indicators', []),
        'completeness': risk_res.get('completeness', 85),
        'breakdown': risk_res.get('breakdown', {}),
        'contributing_factors': risk_res.get('contributing_factors', []),
        'security_checks': risk_res.get('security_checks', []),
        'six_checks': risk_res.get('six_checks', []),
        'extracted_fields': validation_res.get('extracted_fields', []),
        'ai_detection': ai_detection_res,
        'summary_verdict': risk_res.get('summary_verdict', ''),
        'why_this_result': risk_res.get('why_this_result', ''),
        'audit_trail': risk_res.get('audit_trail', [])
    }

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO verification_records (
            verification_code, document_type, document_number, extracted_name,
            risk_score, result, reasons_json, checks_json, ocr_data_json,
            image_analysis_json, fingerprint, fingerprint_status, filename, analyst_user
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        verification_code,
        document_type,
        doc_number if doc_number not in ['Not detected', 'Not confidently detected'] else None,
        extracted_name if extracted_name not in ['Not detected', 'Not confidently detected'] else None,
        risk_res['score'],
        risk_res['status_label'],
        json.dumps(meta_payload),
        json.dumps(risk_res['checks']),
        json.dumps(ocr_data),
        json.dumps(image_analysis_res),
        file_hash,
        fingerprint_res['status'],
        filename,
        analyst_username
    ))
    conn.commit()
    conn.close()

    return verification_code


# ====================================================================
# ROUTES
# ====================================================================

@app.route('/debug-path')
def debug_path():
    return {
        'request.path': request.path,
        'request.url': request.url,
        'request.base_url': request.base_url,
        'environ.PATH_INFO': request.environ.get('PATH_INFO'),
        'environ.SCRIPT_NAME': request.environ.get('SCRIPT_NAME'),
        'headers': dict(request.headers)
    }


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Live dashboard aggregating real SQLite metrics, analytics insights, and recent activity."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Aggregate metric counters
    cursor.execute("SELECT COUNT(*) FROM verification_records")
    total_screened = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%GENUINE%'")
    genuine_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%VERIFICATION%'")
    review_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%SUSPICIOUS%'")
    suspicious_count = cursor.fetchone()[0]

    # Calculate real risk distribution percentages
    if total_screened > 0:
        genuine_pct = round((genuine_count / total_screened) * 100)
        review_pct = round((review_count / total_screened) * 100)
        suspicious_pct = max(0, 100 - genuine_pct - review_pct)
    else:
        genuine_pct, review_pct, suspicious_pct = 0, 0, 0

    risk_dist = {
        'genuine_pct': genuine_pct,
        'review_pct': review_pct,
        'suspicious_pct': suspicious_pct
    }

    # Derive real screening insights from the records
    cursor.execute("SELECT reasons_json, image_analysis_json, result FROM verification_records")
    all_recs = cursor.fetchall()
    
    mismatches_count = 0
    alterations_count = 0
    manual_review_count = review_count

    for r in all_recs:
        r_reasons = r['reasons_json'] or ''
        r_img = r['image_analysis_json'] or ''
        if 'mismatch' in r_reasons.lower() or 'not match' in r_reasons.lower() or 'not registered' in r_reasons.lower():
            mismatches_count += 1
        if '"alteration_detected": true' in r_img:
            alterations_count += 1

    insights = {
        'has_data': total_screened > 0,
        'mismatches_count': mismatches_count,
        'manual_review_count': manual_review_count,
        'alterations_count': alterations_count
    }

    # Document types distribution from real DB
    cursor.execute("SELECT document_type, COUNT(*) as cnt FROM verification_records GROUP BY document_type")
    type_rows = cursor.fetchall()
    doc_types = {row['document_type']: row['cnt'] for row in type_rows}

    # Recent 6 verification logs
    cursor.execute("SELECT * FROM verification_records ORDER BY created_at DESC LIMIT 6")
    recent_records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    stats = {
        'total_screened': total_screened,
        'genuine': genuine_count,
        'requires_review': review_count,
        'suspicious': suspicious_count
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        risk_dist=risk_dist,
        insights=insights,
        doc_types=doc_types,
        recent_records=recent_records
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Analyst authentication with PBKDF2 password hashing & session management."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f"Welcome back, {username}! Verification session armed.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Authentication failed. Invalid credentials (incorrect username or password).", "danger")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Analyst session successfully terminated.", "info")
    return redirect(url_for('login'))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Safely serves uploaded document images across both local and serverless environments."""
    upload_folder = app.config.get('UPLOAD_FOLDER', UPLOAD_FOLDER)
    if os.path.exists(os.path.join(upload_folder, filename)):
        return send_from_directory(upload_folder, filename)
    static_upload = os.path.join(app.root_path, 'static', 'uploads')
    if os.path.exists(os.path.join(static_upload, filename)):
        return send_from_directory(static_upload, filename)
    sample_path = os.path.join(SAMPLE_DOCS_FOLDER, filename)
    if os.path.exists(sample_path):
        return send_from_directory(SAMPLE_DOCS_FOLDER, filename)
    abort(404)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handles document ingestion, file security checks, and invokes screening pipeline."""
    if request.method == 'POST':
        document_type = request.form.get('document_type', 'ID Card')
        if 'document_file' not in request.files:
            flash("No file was submitted in request.", "danger")
            return redirect(request.url)

        file = request.files['document_file']
        if file.filename == '':
            flash("Please choose a document file to screen.", "warning")
            return redirect(request.url)

        if file and is_allowed_file(file.filename):
            safe_name = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(saved_path)

            # Perform preliminary image quality check before fraud screening
            quality_res = check_image_quality(saved_path)
            if not quality_res.get('adequate', True):
                # Clean up temporary uploaded file
                try:
                    if os.path.exists(saved_path):
                        os.remove(saved_path)
                except Exception:
                    pass
                flash("Image quality is insufficient for reliable screening. Please upload a clearer image.", "warning")
                return redirect(request.url)

            analyst = session.get('username', 'Analyst')
            code = run_screening_pipeline(saved_path, document_type, unique_filename, analyst)
            flash("Document screening complete! Review the detailed assessment dossier below.", "success")
            return redirect(url_for('result', code=code))
        else:
            flash("Unsupported file format. Please upload a JPG, JPEG, PNG, or PDF file.", "danger")
            return redirect(request.url)

    return render_template('upload.html')


@app.route('/result/<code>')
def result(code):
    """Displays the explainable document screening assessment report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_records WHERE verification_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Verification record not found.", "warning")
        return redirect(url_for('dashboard'))

    record = dict(row)
    raw_meta = json.loads(record['reasons_json']) if record.get('reasons_json') else []
    if isinstance(raw_meta, dict):
        reasons = raw_meta.get('reasons', [])
        positive_indicators = raw_meta.get('positive_indicators', [])
        attention_indicators = raw_meta.get('attention_indicators', [])
        completeness = raw_meta.get('completeness', 85)
        saved_breakdown = raw_meta.get('breakdown', {})
        contributing_factors = raw_meta.get('contributing_factors', [])
        security_checks = raw_meta.get('security_checks') or raw_meta.get('six_checks', [])
        extracted_fields = raw_meta.get('extracted_fields', [])
        why_this_result = raw_meta.get('why_this_result', '')
        audit_trail = raw_meta.get('audit_trail', [])
    else:
        reasons = raw_meta
        positive_indicators = [r for r in reasons if 'cleanly' in r or 'verified' in r or 'matches' in r or 'valid' in r]
        attention_indicators = [r for r in reasons if r not in positive_indicators]
        completeness = 95 if record['risk_score'] <= 15 else (80 if record['risk_score'] <= 35 else 60)
        saved_breakdown = {}
        contributing_factors = []
        security_checks = []
        extracted_fields = []
        why_this_result = ''
        audit_trail = []

    checks = json.loads(record['checks_json']) if record.get('checks_json') else []
    ocr_data = json.loads(record['ocr_data_json']) if record.get('ocr_data_json') else {}
    image_analysis = json.loads(record['image_analysis_json']) if record.get('image_analysis_json') else {}

    score = record['risk_score']
    # Exact thresholds requested:
    # 0–25: LIKELY GENUINE
    # 26–55: REQUIRES FURTHER VERIFICATION
    # 56+: SUSPICIOUS
    if score <= 25:
        badge_class = "badge-low-risk"
        color_code = "#059669"
        risk_level = "LOW RISK"
    elif score <= 55:
        badge_class = "badge-med-risk"
        color_code = "#D97706"
        risk_level = "MEDIUM RISK"
    else:
        badge_class = "badge-high-risk"
        color_code = "#DC2626"
        risk_level = "HIGH RISK"

    summary_verdict = raw_meta.get('summary_verdict', '') if isinstance(raw_meta, dict) else ''

    if not why_this_result:
        if score <= 25:
            why_this_result = "All required fields were successfully extracted, the document structure was consistent, and no significant alteration or synthetic-document indicators were detected."
        elif score <= 55:
            why_this_result = "Some information could not be fully verified or one or more inconsistencies were detected. Further verification is recommended."
        else:
            why_this_result = "Multiple suspicious indicators were detected during document structure, consistency, alteration, or synthetic-document screening."

    if not extracted_fields:
        doc_num = ocr_data.get('document_number', 'Not detected')
        doc_name = ocr_data.get('name', 'Not detected')
        dob_val = ocr_data.get('dob', 'Not detected')
        issue_val = ocr_data.get('issue_date', 'Not detected')
        exp_val = ocr_data.get('expiry_date', 'Not detected')
        is_exp = any('EXPIRED' in str(c.get('details', '')) for c in checks)
        extracted_fields = [
            {'field': 'Name', 'value': doc_name, 'status': 'Extracted' if doc_name not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': doc_name not in ['Not detected', 'Not confidently detected'], 'icon': 'fa-solid fa-check text-success' if doc_name not in ['Not detected', 'Not confidently detected'] else 'fa-solid fa-triangle-exclamation text-warning'},
            {'field': 'Document Number', 'value': doc_num, 'status': 'Valid Format' if doc_num not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': doc_num not in ['Not detected', 'Not confidently detected'], 'icon': 'fa-solid fa-check text-success' if doc_num not in ['Not detected', 'Not confidently detected'] else 'fa-solid fa-triangle-exclamation text-warning'},
            {'field': 'Date of Birth', 'value': dob_val, 'status': 'Extracted' if dob_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': dob_val not in ['Not detected', 'Not confidently detected'], 'icon': 'fa-solid fa-check text-success' if dob_val not in ['Not detected', 'Not confidently detected'] else 'fa-solid fa-triangle-exclamation text-warning'},
            {'field': 'Issue Date', 'value': issue_val, 'status': 'Extracted' if issue_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': issue_val not in ['Not detected', 'Not confidently detected'], 'icon': 'fa-solid fa-check text-success' if issue_val not in ['Not detected', 'Not confidently detected'] else 'fa-solid fa-triangle-exclamation text-warning'},
            {'field': 'Expiry Date', 'value': exp_val, 'status': 'Expired' if is_exp else ('Valid' if exp_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected'), 'is_valid': not is_exp and exp_val not in ['Not detected', 'Not confidently detected'], 'icon': 'fa-solid fa-circle-xmark text-danger' if is_exp else ('fa-solid fa-check text-success' if exp_val not in ['Not detected', 'Not confidently detected'] else 'fa-solid fa-triangle-exclamation text-warning')},
            {'field': 'Document Type', 'value': record['document_type'], 'status': 'Validated', 'is_valid': True, 'icon': 'fa-solid fa-check text-success'}
        ]

    if not audit_trail:
        audit_trail = [
            {'step': 1, 'name': 'Document Uploaded', 'status': 'Completed', 'icon': 'fa-solid fa-cloud-arrow-up'},
            {'step': 2, 'name': 'Image Quality Checked', 'status': 'Completed', 'icon': 'fa-solid fa-image'},
            {'step': 3, 'name': 'OCR Completed', 'status': 'Completed', 'icon': 'fa-solid fa-font'},
            {'step': 4, 'name': 'Information Extracted', 'status': 'Completed', 'icon': 'fa-solid fa-address-card'},
            {'step': 5, 'name': 'Field Validation Completed', 'status': 'Completed', 'icon': 'fa-solid fa-list-check'},
            {'step': 6, 'name': 'Alteration Screening Completed', 'status': 'Completed', 'icon': 'fa-solid fa-microscope'},
            {'step': 7, 'name': 'Synthetic Indicator Screening Completed', 'status': 'Completed', 'icon': 'fa-solid fa-wand-magic-sparkles'},
            {'step': 8, 'name': 'Risk Assessment Completed', 'status': 'Completed', 'icon': 'fa-solid fa-scale-balanced'},
            {'step': 9, 'name': 'Final Report Generated', 'status': 'Completed', 'icon': 'fa-solid fa-file-shield'}
        ]

    if saved_breakdown and 'total' in saved_breakdown:
        breakdown = saved_breakdown
    else:
        breakdown = {
            'ocr_quality': 0,
            'document_completeness': 0,
            'field_consistency': 0,
            'document_structure': 0,
            'visual_alteration': 0,
            'ai_synthetic': 0,
            'database_verification': 0,
            'total': score
        }

    if not contributing_factors:
        contributing_factors = [
            {'name': 'OCR Quality', 'penalty': breakdown.get('ocr_quality', 0)},
            {'name': 'Missing Information', 'penalty': breakdown.get('document_completeness', 0)},
            {'name': 'Field Inconsistency', 'penalty': breakdown.get('field_consistency', 0)},
            {'name': 'Document Structure', 'penalty': breakdown.get('document_structure', 0)},
            {'name': 'Alteration Indicators', 'penalty': breakdown.get('visual_alteration', 0)},
            {'name': 'Synthetic Indicators', 'penalty': breakdown.get('ai_synthetic', 0)},
            {'name': 'Database Verification', 'penalty': breakdown.get('database_verification', 0)}
        ]

    risk = {
        'score': score,
        'completeness': completeness,
        'risk_level': risk_level,
        'status_label': record['result'],
        'summary_verdict': summary_verdict,
        'why_this_result': why_this_result,
        'badge_class': badge_class,
        'color_code': color_code,
        'reasons': reasons,
        'positive_indicators': positive_indicators,
        'attention_indicators': attention_indicators,
        'security_checks': security_checks,
        'six_checks': security_checks,
        'checks': checks,
        'breakdown': breakdown,
        'contributing_factors': contributing_factors,
        'audit_trail': audit_trail,
        'extracted_fields': extracted_fields
    }

    fingerprint = {
        'fingerprint': record['fingerprint'],
        'status': record['fingerprint_status'],
        'message': f"Status: {record['fingerprint_status']} registered."
    }

    validation = {
        'is_expired': any('EXPIRED' in str(c.get('details', '')) for c in checks),
        'extracted_fields': extracted_fields
    }

    return render_template(
        'result.html',
        record=record,
        risk=risk,
        security_checks=security_checks,
        six_checks=security_checks,
        extracted_fields=extracted_fields,
        why_this_result=why_this_result,
        contributing_factors=contributing_factors,
        audit_trail=audit_trail,
        ai_detection=raw_meta.get('ai_detection', {}) if isinstance(raw_meta, dict) else {},
        ocr=ocr_data,
        image_analysis=image_analysis,
        fingerprint=fingerprint,
        validation=validation
    )


@app.route('/report/<code>')
def report(code):
    """Generates the official Document Security Screening Report suitable for PDF export and printing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_records WHERE verification_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Verification record not found.", "warning")
        return redirect(url_for('dashboard'))

    record = dict(row)
    raw_meta = json.loads(record['reasons_json']) if record.get('reasons_json') else {}
    if not isinstance(raw_meta, dict):
        raw_meta = {}

    ocr_data = json.loads(record['ocr_data_json']) if record.get('ocr_data_json') else {}
    image_analysis = json.loads(record['image_analysis_json']) if record.get('image_analysis_json') else {}
    checks = json.loads(record['checks_json']) if record.get('checks_json') else []

    score = record['risk_score']
    if score <= 25:
        risk_level = "LOW RISK"
        status_label = "LIKELY GENUINE"
        badge_class = "badge-genuine"
        color_code = "#059669"
    elif score <= 55:
        risk_level = "MEDIUM RISK"
        status_label = "REQUIRES FURTHER VERIFICATION"
        badge_class = "badge-review"
        color_code = "#D97706"
    else:
        risk_level = "HIGH RISK"
        status_label = "SUSPICIOUS"
        badge_class = "badge-suspicious"
        color_code = "#DC2626"

    why_this_result = raw_meta.get('why_this_result')
    if not why_this_result:
        if score <= 25:
            why_this_result = "All required fields were successfully extracted, the document structure was consistent, and no significant alteration or synthetic-document indicators were detected."
        elif score <= 55:
            why_this_result = "Some information could not be fully verified or one or more inconsistencies were detected. Further verification is recommended."
        else:
            why_this_result = "Multiple suspicious indicators were detected during document structure, consistency, alteration, or synthetic-document screening."

    security_checks = raw_meta.get('security_checks') or raw_meta.get('six_checks', [])
    extracted_fields = raw_meta.get('extracted_fields', [])
    if not extracted_fields:
        doc_num = ocr_data.get('document_number', 'Not detected')
        doc_name = ocr_data.get('name', 'Not detected')
        dob_val = ocr_data.get('dob', 'Not detected')
        issue_val = ocr_data.get('issue_date', 'Not detected')
        exp_val = ocr_data.get('expiry_date', 'Not detected')
        is_exp = any('EXPIRED' in str(c.get('details', '')) for c in checks)
        extracted_fields = [
            {'field': 'Name', 'value': doc_name, 'status': 'Extracted' if doc_name not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': doc_name not in ['Not detected', 'Not confidently detected']},
            {'field': 'Document Number', 'value': doc_num, 'status': 'Valid Format' if doc_num not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': doc_num not in ['Not detected', 'Not confidently detected']},
            {'field': 'Date of Birth', 'value': dob_val, 'status': 'Extracted' if dob_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': dob_val not in ['Not detected', 'Not confidently detected']},
            {'field': 'Issue Date', 'value': issue_val, 'status': 'Extracted' if issue_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected', 'is_valid': issue_val not in ['Not detected', 'Not confidently detected']},
            {'field': 'Expiry Date', 'value': exp_val, 'status': 'Expired' if is_exp else ('Valid' if exp_val not in ['Not detected', 'Not confidently detected'] else 'Not Detected'), 'is_valid': not is_exp and exp_val not in ['Not detected', 'Not confidently detected']},
            {'field': 'Document Type', 'value': record['document_type'], 'status': 'Validated', 'is_valid': True}
        ]

    contributing_factors = raw_meta.get('contributing_factors', [])
    if not contributing_factors:
        bd = raw_meta.get('breakdown', {})
        contributing_factors = [
            {'name': 'OCR Quality', 'penalty': bd.get('ocr_quality', 0)},
            {'name': 'Missing Information', 'penalty': bd.get('document_completeness', 0)},
            {'name': 'Field Inconsistency', 'penalty': bd.get('field_consistency', 0)},
            {'name': 'Document Structure', 'penalty': bd.get('document_structure', 0)},
            {'name': 'Alteration Indicators', 'penalty': bd.get('visual_alteration', 0)},
            {'name': 'Synthetic Indicators', 'penalty': bd.get('ai_synthetic', 0)},
            {'name': 'Database Verification', 'penalty': bd.get('database_verification', 0)}
        ]

    audit_trail = raw_meta.get('audit_trail', [])
    if not audit_trail:
        audit_trail = [
            {'step': 1, 'name': 'Document Uploaded', 'status': 'Completed'},
            {'step': 2, 'name': 'Image Quality Checked', 'status': 'Completed'},
            {'step': 3, 'name': 'OCR Completed', 'status': 'Completed'},
            {'step': 4, 'name': 'Information Extracted', 'status': 'Completed'},
            {'step': 5, 'name': 'Field Validation Completed', 'status': 'Completed'},
            {'step': 6, 'name': 'Alteration Screening Completed', 'status': 'Completed'},
            {'step': 7, 'name': 'Synthetic Indicator Screening Completed', 'status': 'Completed'},
            {'step': 8, 'name': 'Risk Assessment Completed', 'status': 'Completed'},
            {'step': 9, 'name': 'Final Report Generated', 'status': 'Completed'}
        ]

    return render_template(
        'report_pdf.html',
        record=record,
        score=score,
        risk_level=risk_level,
        status_label=status_label,
        badge_class=badge_class,
        color_code=color_code,
        why_this_result=why_this_result,
        security_checks=security_checks,
        extracted_fields=extracted_fields,
        contributing_factors=contributing_factors,
        audit_trail=audit_trail,
        ocr_data=ocr_data,
        image_analysis=image_analysis,
        date_generated=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )


@app.route('/details/<code>')
def details(code):
    """Detailed historical dossier for a past verification record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM verification_records WHERE verification_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Verification record not found.", "warning")
        return redirect(url_for('history'))

    record = dict(row)
    raw_meta = json.loads(record['reasons_json']) if record.get('reasons_json') else []
    if isinstance(raw_meta, dict):
        reasons = raw_meta.get('reasons', [])
        positive_indicators = raw_meta.get('positive_indicators', [])
        attention_indicators = raw_meta.get('attention_indicators', [])
        completeness = raw_meta.get('completeness', 85)
        six_checks = raw_meta.get('six_checks', [])
        ai_detection = raw_meta.get('ai_detection', {})
        summary_verdict = raw_meta.get('summary_verdict', '')
    else:
        reasons = raw_meta
        positive_indicators = [r for r in reasons if 'cleanly' in r or 'verified' in r or 'matches' in r or 'valid' in r]
        attention_indicators = [r for r in reasons if r not in positive_indicators]
        completeness = 95 if record['risk_score'] <= 15 else (80 if record['risk_score'] <= 35 else 60)
        six_checks = []
        ai_detection = {}
        summary_verdict = ''

    checks = json.loads(record['checks_json']) if record.get('checks_json') else []
    ocr_data = json.loads(record['ocr_data_json']) if record.get('ocr_data_json') else {}
    image_analysis = json.loads(record['image_analysis_json']) if record.get('image_analysis_json') else {}

    return render_template(
        'details.html',
        record=record,
        reasons=reasons,
        positive_indicators=positive_indicators,
        attention_indicators=attention_indicators,
        completeness=completeness,
        six_checks=six_checks,
        ai_detection=ai_detection,
        summary_verdict=summary_verdict,
        checks=checks,
        ocr_data=ocr_data,
        image_analysis=image_analysis
    )


@app.route('/history')
def history():
    """Audit history of all screened identity documents with optional risk filter."""
    filter_risk = request.args.get('filter_risk')
    conn = get_db_connection()
    cursor = conn.cursor()

    if filter_risk:
        cursor.execute("SELECT * FROM verification_records WHERE result LIKE ? ORDER BY created_at DESC", (f"%{filter_risk}%",))
    else:
        cursor.execute("SELECT * FROM verification_records ORDER BY created_at DESC")

    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('history.html', records=records)


@app.route('/reports')
def reports():
    """Executive reporting view summarizing screening volumes, verification rates, and document distribution."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM verification_records")
    total_scans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%GENUINE%'")
    genuine_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%VERIFICATION%'")
    review_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM verification_records WHERE result LIKE '%SUSPICIOUS%'")
    suspicious_count = cursor.fetchone()[0]

    genuine_rate = round((genuine_count / total_scans * 100), 1) if total_scans > 0 else 0
    review_rate = round((review_count / total_scans * 100), 1) if total_scans > 0 else 0
    suspicious_rate = round((suspicious_count / total_scans * 100), 1) if total_scans > 0 else 0

    # Type breakdown
    cursor.execute("SELECT document_type, COUNT(*) as cnt FROM verification_records GROUP BY document_type ORDER BY cnt DESC")
    type_rows = cursor.fetchall()
    
    type_breakdown = []
    rule_map = {
        'ID Card': 'Syntax matching & sample registry validation',
        'Passport': 'Format validation & MRZ syntax rules',
        'Driving Licence': 'Expiry checking & licensing syntax',
        'Certificate': 'Authority verification & layout consistency',
        'College ID': 'Student number structure & registry check',
        'Other': 'General image alteration & integrity check'
    }

    for r in type_rows:
        t_name = r['document_type']
        t_cnt = r['cnt']
        t_share = round((t_cnt / total_scans * 100), 1) if total_scans > 0 else 0
        type_breakdown.append({
            'type': t_name,
            'count': t_cnt,
            'share': t_share,
            'rule': rule_map.get(t_name, 'General security screening')
        })

    conn.close()

    return render_template(
        'reports.html',
        total_scans=total_scans,
        genuine_count=genuine_count,
        review_count=review_count,
        suspicious_count=suspicious_count,
        genuine_rate=genuine_rate,
        review_rate=review_rate,
        suspicious_rate=suspicious_rate,
        type_breakdown=type_breakdown
    )


@app.route('/compare')
def compare():
    """Document comparison feature allowing dual-record attribute and visual comparison."""
    doc1_code = request.args.get('doc1') or request.args.get('base')
    doc2_code = request.args.get('doc2')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT verification_code, document_type, extracted_name, document_number FROM verification_records ORDER BY created_at DESC")
    all_records = [dict(row) for row in cursor.fetchall()]

    doc1 = None
    doc2 = None
    comparisons = []
    diff_count = 0

    if doc1_code:
        cursor.execute("SELECT * FROM verification_records WHERE verification_code = ?", (doc1_code,))
        r1 = cursor.fetchone()
        if r1:
            doc1 = dict(r1)

    if doc2_code:
        cursor.execute("SELECT * FROM verification_records WHERE verification_code = ?", (doc2_code,))
        r2 = cursor.fetchone()
        if r2:
            doc2 = dict(r2)

    conn.close()

    if doc1 and doc2:
        ocr1 = json.loads(doc1['ocr_data_json']) if doc1.get('ocr_data_json') else {}
        ocr2 = json.loads(doc2['ocr_data_json']) if doc2.get('ocr_data_json') else {}
        img1 = json.loads(doc1['image_analysis_json']) if doc1.get('image_analysis_json') else {}
        img2 = json.loads(doc2['image_analysis_json']) if doc2.get('image_analysis_json') else {}

        # Attribute comparisons
        attrs = [
            ("Document Type", doc1.get('document_type'), doc2.get('document_type'), False),
            ("Document Number", ocr1.get('document_number'), ocr2.get('document_number'), False),
            ("Holder Name", ocr1.get('name'), ocr2.get('name'), False),
            ("Date of Birth", ocr1.get('dob'), ocr2.get('dob'), False),
            ("Expiry Date", ocr1.get('expiry_date'), ocr2.get('expiry_date'), False),
            ("Integrity Hash (SHA-256)", doc1.get('fingerprint'), doc2.get('fingerprint'), True),
            ("Layout Blur Score", str(img1.get('blur_score')), str(img2.get('blur_score')), False),
            ("Alteration Screening Verdict", doc1.get('result'), doc2.get('result'), False)
        ]

        for label, val1, val2, is_code in attrs:
            v1_clean = str(val1).strip().lower() if val1 else ''
            v2_clean = str(val2).strip().lower() if val2 else ''
            matches = (v1_clean == v2_clean)
            if not matches:
                diff_count += 1
            comparisons.append({
                'attribute': label,
                'val1': val1,
                'val2': val2,
                'match': matches,
                'is_code': is_code
            })

    return render_template(
        'compare.html',
        all_records=all_records,
        doc1=doc1,
        doc2=doc2,
        doc1_code=doc1_code,
        doc2_code=doc2_code,
        comparisons=comparisons,
        diff_count=diff_count
    )


@app.route('/help')
def help_page():
    """Help documentation and viva cheat sheet (aliased to about)."""
    return render_template('about.html')


@app.route('/about')
def about():
    """Academic synopsis and college viva reference notes."""
    return render_template('about.html')


@app.route('/quick-demo/<test_name>')
def run_quick_demo(test_name):
    """
    Demonstration helper for College Viva and rapid testing.
    Runs pre-generated synthetic identity documents through the screening pipeline.
    """
    demos = {
        'clean': {
            'file': 'TEST1_clean_sample.png',
            'type': 'ID Card',
            'label': 'Clean Sample (Likely Genuine)'
        },
        'altered': {
            'file': 'TEST2_altered_sample.png',
            'type': 'Passport',
            'label': 'Altered Document (Suspicious)'
        },
        'ai_synthetic': {
            'file': 'TEST3_ai_synthetic_sample.png',
            'type': 'ID Card',
            'label': 'AI-Generated Sample (Suspicious)'
        },
        'incomplete': {
            'file': 'TEST4_incomplete_sample.png',
            'type': 'ID Card',
            'label': 'Incomplete Sample (Requires Further Verification)'
        },
        'expired': {
            'file': 'TEST5_expired_sample.png',
            'type': 'Driving Licence',
            'label': 'Expired Document (Requires Further Verification)'
        },
        # Legacy aliases
        'valid': {
            'file': 'TEST1_clean_sample.png',
            'type': 'ID Card',
            'label': 'Clean Sample'
        },
        'tampered': {
            'file': 'TEST2_altered_sample.png',
            'type': 'Passport',
            'label': 'Altered Document'
        },
        'unregistered': {
            'file': 'TEST4_incomplete_sample.png',
            'type': 'ID Card',
            'label': 'Incomplete Sample'
        }
    }

    demo_cfg = demos.get(test_name)
    if not demo_cfg:
        flash("Unknown test scenario selected.", "warning")
        return redirect(url_for('dashboard'))

    src_path = os.path.join(SAMPLE_DOCS_FOLDER, demo_cfg['file'])
    if not os.path.exists(src_path):
        flash(f"Sample file {demo_cfg['file']} not found. Please run sample generator.", "danger")
        return redirect(url_for('dashboard'))

    # Copy to uploads
    dest_filename = f"demo_{uuid.uuid4().hex[:6]}_{demo_cfg['file']}"
    dest_path = os.path.join(app.config['UPLOAD_FOLDER'], dest_filename)
    shutil.copyfile(src_path, dest_path)

    # Execute full pipeline
    code = run_screening_pipeline(dest_path, demo_cfg['type'], dest_filename, session.get('username', 'Demo-Analyst'))
    flash(f"Demo Test '{test_name.upper()}' screened successfully! Review assessment dossier below.", "info")
    return redirect(url_for('result', code=code))


# ====================================================================
# ERROR HANDLERS
# ====================================================================

@app.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('dashboard'))


@app.errorhandler(413)
def file_too_large(error):
    flash("Security Alert: Uploaded file exceeds the 5MB size threshold.", "danger")
    return redirect(url_for('upload'))


# ====================================================================
# SERVER LAUNCHER
# ====================================================================

if __name__ == '__main__':
    print("AI-Based Fake Identity & Document Screening System")
    print("Document Security Platform running at: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
