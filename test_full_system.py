"""
Comprehensive Automated Test Suite for AI Fake Identity Screening System
Tests all 5 test scenarios, score calibration tiers, and 6 Independent Checks:
1. TEST1 (Clean Sample) -> LIKELY GENUINE / LOW RISK (Score <= 25)
2. TEST2 (Altered Document) -> SUSPICIOUS / HIGH RISK (Score >= 56)
3. TEST3 (AI-Generated Sample) -> SUSPICIOUS / HIGH RISK (Score >= 56)
4. TEST4 (Incomplete Sample) -> REQUIRES FURTHER VERIFICATION / MEDIUM RISK (Score 26-55)
5. TEST5 (Expired Document) -> REQUIRES FURTHER VERIFICATION / MEDIUM RISK (Score 26-55)
"""

from app import app
from database import get_db_connection, verify_user
import re


def extract_score(html_data):
    """Extracts score from result page HTML."""
    match = re.search(r'(\d+)\s*<span[^>]*>\s*/\s*100</span>', html_data)
    if match:
        return int(match.group(1))
    return -1


def run_full_test():
    client = app.test_client()

    print("==================================================")
    print("RUNNING COMPREHENSIVE 6-CHECK SYSTEM VERIFICATION")
    print("==================================================")

    # 1. Test Authentication
    user = verify_user("admin", "admin123")
    assert user is not None, "Admin authentication failed!"
    print("[PASS] 1. User Authentication: PBKDF2 verification succeeded.")

    # 2. Test Scenario 1: Clean Sample Document
    res1 = client.get('/quick-demo/clean', follow_redirects=True)
    assert res1.status_code == 200, f"Demo clean failed with {res1.status_code}"
    html1 = res1.data.decode('utf-8', errors='ignore')
    score1 = extract_score(html1)
    print(f"       TEST 1 Score: {score1}/100")
    assert score1 <= 25, f"Clean sample score expected <= 25, got {score1}"
    assert "Likely Genuine" in html1 or "LIKELY GENUINE" in html1, "Expected 'Likely Genuine' label"
    assert "All required fields were successfully extracted" in html1 or "No significant suspicious indicators detected" in html1
    assert "Security Checks" in html1
    print("[PASS] 2. TEST 1 (Clean Sample): Correctly scored <= 25 -> LIKELY GENUINE.")

    # 3. Test Scenario 2: Altered / Tampered Document
    res2 = client.get('/quick-demo/altered', follow_redirects=True)
    assert res2.status_code == 200
    html2 = res2.data.decode('utf-8', errors='ignore')
    score2 = extract_score(html2)
    print(f"       TEST 2 Score: {score2}/100")
    assert score2 >= 56, f"Altered document score expected >= 56, got {score2}"
    assert "Suspicious" in html2 or "SUSPICIOUS" in html2, "Expected 'Suspicious' label"
    assert "Alteration Screening" in html2 or "Visual Alteration" in html2
    print("[PASS] 3. TEST 2 (Altered Document): Correctly scored >= 56 -> SUSPICIOUS.")

    # 4. Test Scenario 3: AI-Generated / Synthetic Sample ID
    res3 = client.get('/quick-demo/ai_synthetic', follow_redirects=True)
    assert res3.status_code == 200
    html3 = res3.data.decode('utf-8', errors='ignore')
    score3 = extract_score(html3)
    print(f"       TEST 3 Score: {score3}/100")
    assert score3 >= 56, f"AI-generated document score expected >= 56, got {score3}"
    assert "Suspicious" in html3 or "SUSPICIOUS" in html3, "Expected 'Suspicious' label"
    assert "AI/Synthetic Indicators" in html3 or "AI & Synthetic Document Indicators" in html3
    print("[PASS] 4. TEST 3 (AI-Generated Document): Correctly scored >= 56 -> SUSPICIOUS.")

    # 5. Test Scenario 4: Incomplete / Missing Fields Document
    res4 = client.get('/quick-demo/incomplete', follow_redirects=True)
    assert res4.status_code == 200
    html4 = res4.data.decode('utf-8', errors='ignore')
    score4 = extract_score(html4)
    print(f"       TEST 4 Score: {score4}/100")
    assert 26 <= score4 <= 55, f"Incomplete document score expected 26-55, got {score4}"
    assert "Requires Further Verification" in html4 or "REQUIRES FURTHER VERIFICATION" in html4, "Expected 'Requires Further Verification' label"
    assert "Suspicious / High Risk" not in html4, "Incomplete document must NOT be marked Suspicious!"
    print("[PASS] 5. TEST 4 (Incomplete Document): Correctly scored 26-55 -> REQUIRES FURTHER VERIFICATION.")

    # 6. Test Scenario 5: Expired Document
    res5 = client.get('/quick-demo/expired', follow_redirects=True)
    assert res5.status_code == 200
    html5 = res5.data.decode('utf-8', errors='ignore')
    score5 = extract_score(html5)
    print(f"       TEST 5 Score: {score5}/100")
    assert 26 <= score5 <= 55, f"Expired document score expected 26-55, got {score5}"
    assert "Requires Further Verification" in html5 or "REQUIRES FURTHER VERIFICATION" in html5, "Expected 'Requires Further Verification' label"
    assert "EXPIRED" in html5
    print("[PASS] 6. TEST 5 (Expired Document): Correctly scored 26-55 -> REQUIRES FURTHER VERIFICATION.")

    # 7. Test Dashboard queries
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    assert b"Document Security Center" in res_dash.data
    print("[PASS] 7. Dashboard: Document Security Center & live analytics loaded.")

    # 8. Test History queries (both default and pre-filtered)
    res_hist = client.get('/history')
    assert res_hist.status_code == 200
    assert b"Screening History" in res_hist.data or b"Historical Document Screenings" in res_hist.data
    print("[PASS] 8. Audit History: Historical table with search and filter loaded.")

    res_hist_filtered = client.get('/history?filter_risk=GENUINE')
    assert res_hist_filtered.status_code == 200
    print("[PASS]    Filtered History: URL query filter (?filter_risk=GENUINE) loaded.")

    # 9. Test Reports route & Printable PDF Report
    res_reports = client.get('/reports')
    assert res_reports.status_code == 200
    assert b"Screening Reports &amp; Metrics" in res_reports.data or b"Screening Reports & Metrics" in res_reports.data
    print("[PASS] 9. Reports Module: Executive summary & risk distribution loaded.")

    # 10. Test Compare route
    res_compare = client.get('/compare')
    assert res_compare.status_code == 200
    assert b"Document Comparison" in res_compare.data
    print("[PASS] 10. Compare Module: Side-by-side comparison interface loaded.")

    # 11. Test Help route
    res_help = client.get('/help')
    assert res_help.status_code == 200
    assert b"Viva Voce" in res_help.data
    print("[PASS] 11. Help Module: Viva Voce cheat sheet & methodology loaded.")

    # 12. Check database rows
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), verification_code FROM verification_records")
    row = c.fetchone()
    count = row[0]
    sample_code = row[1]
    conn.close()
    assert count >= 5, f"Expected at least 5 records, got {count}"
    print(f"[PASS] 12. Database Persistence: {count} verification records saved in SQLite.")

    # 13. Test Dedicated PDF Screening Report
    res_pdf = client.get(f'/report/{sample_code}')
    assert res_pdf.status_code == 200
    assert b"Document Security Screening Report" in res_pdf.data
    assert b"This report provides an automated preliminary screening assessment" in res_pdf.data
    print(f"[PASS] 13. Dedicated Screening Report: Printable PDF view rendered for {sample_code}.")

    # 14. Test Image Quality Assessment
    from utils.image_analysis import check_image_quality
    import numpy as np
    import cv2
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tf:
        bad_img = np.zeros((100, 100, 3), dtype=np.uint8) # tiny, black, blurry, no text
        cv2.imwrite(tf.name, bad_img)
        quality = check_image_quality(tf.name)
        assert not quality['adequate'], "Black tiny image should fail image quality check"
        assert len(quality['issues']) >= 1
        assert "insufficient for reliable screening" in quality['message']
        print(f"[PASS] 14. Image Quality Check: Insufficient image correctly caught -> {quality['issues']}")

    print("\n==================================================")
    print("ALL 14 TESTS PASSED! FULL SYSTEM VERIFIED!")
    print("==================================================")


if __name__ == '__main__':
    run_full_test()

