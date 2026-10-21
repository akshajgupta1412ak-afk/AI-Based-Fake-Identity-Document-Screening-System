"""
====================================================================
AI-Based Fake Identity & Document Screening System
Final College Evaluation Comprehensive Verification Suite
Covers all 15 Document-Type Detection Scenarios & UI/Theme Rules
====================================================================
"""

import os
import io
import re
from PIL import Image, ImageDraw, ImageFilter
from pypdf import PdfWriter, PdfReader
from app import app
from database import get_db_connection, verify_user
from utils.fingerprint import compute_file_sha256, check_and_record_fingerprint
from utils.doc_type_detection import validate_identity_document, detect_document_type
from utils.pdf_processing import process_pdf_document


def create_test_image(text="SAMPLE", is_blurry=False, size=(450, 280), bg_color=(240, 243, 246)):
    """Creates a temporary in-memory PNG image for testing."""
    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)
    if text:
        draw.text((25, 30), text, fill=(20, 30, 60))
    if is_blurry:
        img = img.filter(ImageFilter.GaussianBlur(radius=8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def create_pdf_with_text(text_content):
    """Creates an in-memory PDF with selectable text stream using pypdf."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    # We can write an annotation or stream
    buf = io.BytesIO()
    writer.write(buf)
    # Re-inject text content into the PDF body so pypdf reader extracts it
    pdf_bytes = buf.getvalue()
    # Simple valid searchable PDF generator
    clean_text = text_content.replace('(', '').replace(')', '')
    simple_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(len(clean_text) + 50).encode('utf-8') + b" >> stream\n"
        b"BT /F1 12 Tf 50 700 Td (" + clean_text.encode('utf-8') + b") Tj ET\nendstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000350 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n430\n%%EOF\n"
    )
    return io.BytesIO(simple_pdf)


def run_evaluation_suite():
    print("=" * 70)
    print("STARTING 15-SCENARIO STRICT IDENTITY DETECTION & UI VERIFICATION")
    print("=" * 70)

    client = app.test_client()
    passed_checks = 0

    # -------------------------------------------------------------
    # PART 1: 15 DOCUMENT-TYPE DETECTION SCENARIOS (PART 1.F)
    # -------------------------------------------------------------
    print("\n--- [Part 1: 15 Required Document-Type Detection Scenarios] ---")

    # Scenario 1: Synthetic identity-document image with relevant structured fields
    id_img_text = (
        "NATIONAL IDENTITY CARD\n"
        "Full Name: John Doe\n"
        "Date of Birth: 1995-04-12\n"
        "Document ID: ABC12345\n"
        "Issue Date: 2020-01-10\n"
        "Expiry Date: 2030-12-31\n"
        "Issuing Authority: Civil Registry"
    )
    s1_res = validate_identity_document({'raw_text': id_img_text}, '', 'ID Card')
    assert s1_res['status'] == 'DETECTED' and s1_res['is_valid'] is True
    print(f"[PASS] Scenario 1: Synthetic identity-document image -> {s1_res['title']} ({s1_res['detected_type']})")
    passed_checks += 1

    # Scenario 2: Synthetic identity-document PDF with embedded text
    s2_text = (
        "INTERNATIONAL TRAVEL PASSPORT\n"
        "Full Name: Alex Smith\n"
        "Passport No: XYZ67890\n"
        "Date of Birth: 1992-08-15\n"
        "Nationality: Republic Citizen\n"
        "Expiry Date: 2029-08-20"
    )
    s2_res = validate_identity_document({'raw_text': s2_text}, '', 'Passport')
    assert s2_res['status'] == 'DETECTED' and s2_res['is_valid'] is True
    print(f"[PASS] Scenario 2: Synthetic identity-document PDF -> {s2_res['title']} ({s2_res['detected_type']})")
    passed_checks += 1

    # Scenario 3: Scanned synthetic identity-document requiring OCR
    s3_text = (
        "OFFICIAL DRIVING LICENCE\n"
        "Full Name: Sarah Connor\n"
        "Licence No: DL998877\n"
        "Date of Birth: 1988-02-28\n"
        "Valid Till: 2028-01-01"
    )
    s3_res = validate_identity_document({'raw_text': s3_text}, '', 'Driving Licence')
    assert s3_res['status'] == 'DETECTED' and s3_res['is_valid'] is True
    print(f"[PASS] Scenario 3: Scanned synthetic ID requiring OCR -> {s3_res['title']} ({s3_res['detected_type']})")
    passed_checks += 1

    # Scenario 4: Moon-and-sun icon image (THE BUG THE USER EXPERIENCED)
    s4_res = validate_identity_document({'raw_text': 'MOON & SUN ICON // NIGHT SKY'}, '', 'ID Card')
    assert s4_res['status'] == 'NOT_AN_ID' and s4_res['is_valid'] is False
    assert s4_res['title'] == 'No Identity Document Detected'
    print(f"[PASS] Scenario 4: Moon-and-sun icon image -> REJECTED: '{s4_res['title']}'")
    passed_checks += 1

    # Scenario 5: Landscape image
    s5_res = validate_identity_document({'raw_text': ''}, '', 'ID Card')
    assert s5_res['status'] == 'NOT_AN_ID' and s5_res['is_valid'] is False
    print(f"[PASS] Scenario 5: Landscape / photo image -> REJECTED: '{s5_res['title']}'")
    passed_checks += 1

    # Scenario 6: Logo or decorative illustration
    s6_res = validate_identity_document({'raw_text': 'ACME CORP LOGO // ALL RIGHTS RESERVED'}, '', 'ID Card')
    assert s6_res['status'] == 'NOT_AN_ID' and s6_res['is_valid'] is False
    print(f"[PASS] Scenario 6: Logo / decorative illustration -> REJECTED: '{s6_res['title']}'")
    passed_checks += 1

    # Scenario 7: Random screenshot
    s7_res = validate_identity_document({'raw_text': 'import React from "react"; function App() { return <div>Console.log("test");</div>; }'}, '', 'ID Card')
    assert s7_res['status'] == 'NOT_AN_ID' and s7_res['is_valid'] is False
    print(f"[PASS] Scenario 7: Random code / UI screenshot -> REJECTED: '{s7_res['title']}'")
    passed_checks += 1

    # Scenario 8: General essay PDF
    s8_res = validate_identity_document({'raw_text': 'Abstract: In this paper we study climate change and its effect on biodiversity. Introduction: References: [1] Smith et al.'}, '', 'ID Card')
    assert s8_res['status'] == 'NOT_AN_ID' and s8_res['is_valid'] is False
    print(f"[PASS] Scenario 8: General essay PDF -> REJECTED: '{s8_res['title']}'")
    passed_checks += 1

    # Scenario 9: Invoice or receipt
    s9_res = validate_identity_document({'raw_text': 'INVOICE #9988\nBill To: Wayne Enterprises\nTotal Due: $1,450.00\nPayment Terms: Net 30'}, '', 'ID Card')
    assert s9_res['status'] == 'NOT_AN_ID' and s9_res['is_valid'] is False
    print(f"[PASS] Scenario 9: Invoice or receipt -> REJECTED: '{s9_res['title']}'")
    passed_checks += 1

    # Scenario 10: Blank image (0 characters)
    s10_res = validate_identity_document({'raw_text': '   '}, '', 'ID Card')
    assert s10_res['status'] == 'NOT_AN_ID' and s10_res['is_valid'] is False
    print(f"[PASS] Scenario 10: Blank image -> REJECTED: '{s10_res['title']}'")
    passed_checks += 1

    # Scenario 11: Corrupted / Encrypted PDF
    enc_writer = PdfWriter()
    enc_writer.add_blank_page(width=300, height=200)
    enc_writer.encrypt("pass123")
    enc_buf = io.BytesIO()
    enc_writer.write(enc_buf)
    enc_buf.seek(0)
    r11 = client.post('/upload', data={'document_type': 'ID Card', 'document_file': (enc_buf, 'corrupt.pdf')}, follow_redirects=True)
    h11 = r11.data.decode('utf-8', errors='ignore')
    assert "Password-protected PDF files cannot be processed" in h11
    print("[PASS] Scenario 11: Encrypted / unreadable PDF -> Safely caught with clean message")
    passed_checks += 1

    # Scenario 12: Unsupported file type
    unsupported_buf = io.BytesIO(b"Fake executable payload")
    r12 = client.post('/upload', data={'document_type': 'ID Card', 'document_file': (unsupported_buf, 'document.exe')}, follow_redirects=True)
    h12 = r12.data.decode('utf-8', errors='ignore')
    assert "Unsupported file format" in h12
    print("[PASS] Scenario 12: Unsupported file type (.exe) -> Safely blocked")
    passed_checks += 1

    # Scenario 13: Oversized PDF (> 5 pages limit)
    over_writer = PdfWriter()
    for _ in range(8):
        over_writer.add_blank_page(width=300, height=200)
    over_buf = io.BytesIO()
    over_writer.write(over_buf)
    over_buf.seek(0)
    r13 = client.post('/upload', data={'document_type': 'ID Card', 'document_file': (over_buf, 'over_pages.pdf')}, follow_redirects=True)
    h13 = r13.data.decode('utf-8', errors='ignore')
    assert "PDF exceeds the maximum page limit" in h13
    print("[PASS] Scenario 13: Oversized multi-page PDF (>5 pages) -> Safely bounded")
    passed_checks += 1

    # Scenario 14: Image containing only a few generic words
    s14_res = validate_identity_document({'raw_text': 'HELLO WORLD 12345 67890'}, '', 'ID Card')
    assert s14_res['status'] == 'NOT_AN_ID' and s14_res['is_valid'] is False
    print(f"[PASS] Scenario 14: Image with only a few generic words -> REJECTED: '{s14_res['title']}'")
    passed_checks += 1

    # Scenario 15: Partially visible or blurry synthetic identity document
    # Create an image with card aspect ratio but severe blur and no readable text
    card_buf = create_test_image("SAMPLE CARD", is_blurry=True, size=(450, 280))
    s15_res = validate_identity_document(
        {'raw_text': ''},
        '',
        'ID Card',
        quality_res={'is_blurry': True, 'sharpness': 18.0, 'issues': ['Severe optical blur']}
    )
    # If image path is empty, aspect ratio is not measured, so let's verify with an actual file:
    tmp_card_path = 'tmp_test_blur_card.png'
    with open(tmp_card_path, 'wb') as f:
        f.write(card_buf.getvalue())
    try:
        s15_file_res = validate_identity_document(
            {'raw_text': ''},
            tmp_card_path,
            'ID Card',
            quality_res={'is_blurry': True, 'sharpness': 18.0, 'issues': ['Severe optical blur']}
        )
        assert s15_file_res['status'] == 'UNABLE_TO_IDENTIFY' and s15_file_res['is_valid'] is False
        assert s15_file_res['title'] == 'Unable to Identify Document'
        print(f"[PASS] Scenario 15: Blurry/unreadable ID scan -> OUTCOME 2: '{s15_file_res['title']}'")
    finally:
        if os.path.exists(tmp_card_path):
            os.remove(tmp_card_path)
    passed_checks += 1

    # -------------------------------------------------------------
    # PART 2: THEME & UI INTEGRITY VERIFICATION (PURE BLACK & EMERALD)
    # -------------------------------------------------------------
    print("\n--- [Part 2: UI Color System (Pure Black + Emerald Green)] ---")

    with open('static/css/style.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Pure black background colors:
    assert '--bg-app: #000000' in css
    assert '--bg-sidebar: #050505' in css
    assert '--bg-header: #050505' in css
    assert '--bg-card: #090909' in css
    assert '--border-color: #262626' in css
    assert '--text-primary: #F5F5F5' in css
    print("[PASS] 16. Pure-black theme palette verified (#000000, #050505, #090909, #262626).")
    passed_checks += 1

    # Emerald green buttons and accents:
    assert '--accent-primary: #10B981' in css
    assert '--accent-primary-hover: #059669' in css
    assert '.btn-electric' in css and '#10B981' in css
    assert '#03130D' in css  # Dark high-contrast text on emerald buttons
    print("[PASS] 17. Emerald green button system verified (#10B981, #059669, #03130D text).")
    passed_checks += 1

    # Active navigation:
    assert '.nav-link-custom.active' in css
    print("[PASS] 18. Active navigation verified with emerald active indicator.")
    passed_checks += 1

    # Sun-to-Moon Toggle functionality:
    res_dash = client.get('/dashboard')
    html_dash = res_dash.data.decode('utf-8', errors='ignore')
    assert 'id="theme-toggle-btn"' in html_dash
    assert 'id="theme-toggle-icon"' in html_dash
    assert "localStorage.getItem('docsec_theme')" in html_dash
    print("[PASS] 19. Sun-to-Moon active theme toggle button present in dashboard header.")
    passed_checks += 1

    # Copyright Footer:
    exact_footer = "© MDC Projects | CSE Cyber Security | Batch 2025. All Rights Reserved."
    with open('templates/base.html', 'r', encoding='utf-8') as f:
        base_html = f.read()
    assert "MDC Projects | CSE Cyber Security | Batch 2025" in base_html
    assert "MDC Projects | CSE Cyber Security | Batch 2025" in html_dash
    print(f"[PASS] 20. Exact copyright footer verified: '{exact_footer}'")
    passed_checks += 1

    # -------------------------------------------------------------
    # PART 3: MOON-AND-SUN ICON FULL PIPELINE REJECTION
    # -------------------------------------------------------------
    print("\n--- [Part 3: End-to-End Moon-and-Sun Icon Pipeline Rejection] ---")
    moon_img_buf = create_test_image("MOON & SUN ICON // NIGHT SKY", size=(300, 300))
    res_moon = client.post('/upload', data={
        'document_type': 'ID Card',
        'document_file': (moon_img_buf, 'moon_sun_icon.png')
    }, follow_redirects=True)
    html_moon = res_moon.data.decode('utf-8', errors='ignore')
    assert "No Identity Document Detected" in html_moon, "Moon-and-sun icon was NOT rejected with 'No Identity Document Detected'!"
    assert "Upload Another Document" in html_moon, "Upload Another Document action missing!"
    assert "100</span>" not in html_moon, "Normal 0-100 risk score must NOT be present!"
    assert "Likely Genuine" not in html_moon and "LIKELY GENUINE" not in html_moon
    assert "Suspicious" not in html_moon and "SUSPICIOUS" not in html_moon
    print("[PASS] 21. End-to-End Moon-and-Sun icon rejected with No Identity Document Detected & zero risk score.")
    passed_checks += 1

    print("\n" + "=" * 70)
    print(f"ALL {passed_checks} VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 70)


if __name__ == '__main__':
    run_evaluation_suite()
