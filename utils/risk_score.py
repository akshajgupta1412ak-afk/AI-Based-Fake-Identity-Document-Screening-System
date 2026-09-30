"""
====================================================================
Comprehensive Multi-Factor Risk Assessment Engine
Calculates risk based on combined evidence across 6 Independent Checks:
1. OCR Quality (PASSED / WARNING / FLAGGED)
2. Document Completeness (PASSED / WARNING / FLAGGED)
3. Field Consistency (PASSED / WARNING / FLAGGED)
4. Visual Alteration Check (PASSED / WARNING / FLAGGED)
5. AI/Synthetic Indicators (PASSED / WARNING / FLAGGED)
6. Database Verification (PASSED / WARNING / FLAGGED)

Strict Point Schedule:
Strong suspicious evidence:
- Clear visual tampering: +30
- Strong field inconsistency: +25
- Multiple synthetic/AI indicators: +30
- Invalid document structure: +20
- Major document information mismatch: +25

Moderate evidence:
- Missing important field: +10
- Expired document: +10
- Database mismatch: +15
- Database record unavailable: +5
- OCR uncertainty: +5
- Minor visual anomaly: +5

Classification Thresholds:
- 0–25: LIKELY GENUINE ("No significant suspicious indicators detected.")
- 26–55: REQUIRES FURTHER VERIFICATION ("Some inconsistencies or insufficient verification evidence were detected.")
- 56+: SUSPICIOUS ("Multiple suspicious indicators were detected.")
====================================================================
"""


def calculate_risk_score(ocr_res, validation_res, image_res, ai_res, fingerprint_res):
    """
    Computes calibrated risk score, verification completeness, and the 6-check breakdown.
    Does NOT depend on a single check. Combines evidence objectively.
    """
    raw_risk = 0
    verification_completeness = 0

    reasons = []
    positive_indicators = []
    attention_indicators = []

    # -------------------------------------------------------------
    # 1. OCR QUALITY CHECK
    # -------------------------------------------------------------
    ocr_status = ocr_res.get('ocr_status', 'PASSED')
    ocr_penalty = ocr_res.get('ocr_penalty', 0)
    ocr_details = ocr_res.get('ocr_details', 'OCR completed.')

    raw_risk += ocr_penalty
    if ocr_status == 'PASSED':
        positive_indicators.append("OCR Quality: High optical text legibility; key identity fields readable.")
        verification_completeness += 20
    elif ocr_status == 'WARNING':
        attention_indicators.append("OCR Quality: Partial text extraction; one or more fields are uncertain.")
        verification_completeness += 10
        reasons.append(f"OCR Uncertainty: {ocr_details}")
    else:
        attention_indicators.append("OCR Quality: Poor optical character legibility or unreadable scan.")
        reasons.append(f"OCR Legibility Flag: {ocr_details}")

    # -------------------------------------------------------------
    # 2. DOCUMENT COMPLETENESS CHECK
    # -------------------------------------------------------------
    comp_check = validation_res.get('completeness_check', {})
    comp_status = comp_check.get('status', 'PASSED')
    comp_penalty = comp_check.get('penalty', 0)
    comp_details = comp_check.get('details', 'All fields present.')

    raw_risk += comp_penalty
    if comp_status == 'PASSED':
        positive_indicators.append("Document Completeness: All expected identity fields are present.")
        verification_completeness += 25
    elif comp_status == 'WARNING':
        attention_indicators.append(f"Document Completeness: {comp_details}")
        verification_completeness += 12
        reasons.append(f"Missing Information: {comp_details}")
    else:
        attention_indicators.append(f"Document Completeness: Structural omission — {comp_details}")
        reasons.append(f"Invalid Structure: {comp_details}")

    # -------------------------------------------------------------
    # 3. FIELD CONSISTENCY CHECK
    # -------------------------------------------------------------
    cons_check = validation_res.get('consistency_check', {})
    cons_status = cons_check.get('status', 'PASSED')
    cons_penalty = cons_check.get('penalty', 0)
    cons_details = cons_check.get('details', 'Field data internally consistent.')

    raw_risk += cons_penalty
    if cons_status == 'PASSED':
        positive_indicators.append("Field Consistency: Date chronology and document syntax conform to standards.")
        verification_completeness += 20
    elif cons_status == 'WARNING':
        attention_indicators.append(f"Field Consistency: {cons_details}")
        verification_completeness += 10
        reasons.append(f"Format Variation: {cons_details}")
    else:
        attention_indicators.append(f"Field Consistency: Strong data contradiction — {cons_details}")
        reasons.append(f"Field Inconsistency: {cons_details}")

    # -------------------------------------------------------------
    # 3b. DOCUMENT STRUCTURE CHECK
    # -------------------------------------------------------------
    struct_check = validation_res.get('structure_check', {})
    struct_status = struct_check.get('status', 'PASSED')
    struct_penalty = struct_check.get('penalty', 0)
    struct_details = struct_check.get('details', 'Standard document layout and structure.')

    raw_risk += struct_penalty
    if struct_status == 'PASSED':
        positive_indicators.append("Document Structure: Header, security margins, and layout conform to standard format.")
    elif struct_status == 'WARNING':
        attention_indicators.append(f"Document Structure: {struct_details}")
    elif struct_status == 'FLAGGED':
        attention_indicators.append(f"Document Structure: {struct_details}")
        reasons.append(f"Structure Flag: {struct_details}")

    # -------------------------------------------------------------
    # 4. VISUAL ALTERATION SCREENING (OpenCV)
    # -------------------------------------------------------------
    vis_status = image_res.get('visual_status', 'PASSED')
    vis_penalty = image_res.get('risk_penalty', 0)
    vis_details = image_res.get('details', 'No alteration detected.')

    raw_risk += vis_penalty
    if vis_status == 'PASSED':
        positive_indicators.append("Alteration Screening: No spliced patches, overlaid boxes, or compression anomalies.")
        verification_completeness += 15
    elif vis_status == 'WARNING':
        attention_indicators.append("Alteration Screening: Minor visual anomaly or localized compression variance.")
        reasons.append(f"Visual Anomaly: {vis_details}")
    else:
        attention_indicators.append("Alteration Screening: Spliced patch or extreme compression disparity detected.")
        reasons.append(f"Visual Alteration: {vis_details}")

    # -------------------------------------------------------------
    # 5. AI / SYNTHETIC INDICATORS CHECK
    # -------------------------------------------------------------
    ai_status = ai_res.get('status', 'PASSED')
    ai_penalty = ai_res.get('risk_penalty', 0)
    ai_details = ai_res.get('details', 'No synthetic indicators detected.')

    raw_risk += ai_penalty
    if ai_status == 'PASSED':
        positive_indicators.append("AI/Synthetic Indicators: Clean typography alignment and natural document composition.")
    elif ai_status == 'WARNING':
        attention_indicators.append(f"AI/Synthetic Indicators: {ai_details}")
        reasons.append(f"Synthetic Anomaly: {ai_details}")
    else:
        attention_indicators.append(f"AI/Synthetic Indicators: Multiple generative artifacts identified — {ai_details}")
        reasons.append(f"Synthetic Indicators: {ai_details}")

    # -------------------------------------------------------------
    # 6. DATABASE VERIFICATION CHECK
    # -------------------------------------------------------------
    db_check = validation_res.get('database_check', {})
    db_status = db_check.get('status', 'NOT VERIFIED')
    db_penalty = db_check.get('penalty', 5)
    db_details = db_check.get('details', 'Registry check complete.')

    raw_risk += db_penalty
    if db_status == 'PASSED':
        positive_indicators.append("Database Verification: Record verified against official reference registry.")
        verification_completeness += 20
    elif db_status in ['NOT VERIFIED', 'WARNING']:
        # Unregistered: Absence of verification, NOT fraud!
        attention_indicators.append("Database Verification: Record not found in local sample database (unverified).")
        verification_completeness += 5
        reasons.append("Database Verification: Not found in reference registry (requires verification).")
    else:
        attention_indicators.append(f"Database Verification: Information conflict or blacklisted ID — {db_details}")
        reasons.append(f"Database Flag: {db_details}")

    # -------------------------------------------------------------
    # ADDITIONAL CRITERIA: EXPIRATION & FINGERPRINT
    # -------------------------------------------------------------
    if validation_res.get('is_expired'):
        raw_risk += 10  # Moderate evidence: Expired document (+10)
        attention_indicators.append("Validity Check: Document has expired.")
        reasons.append("Validity Check: Document expiration date has lapsed.")
    else:
        positive_indicators.append("Validity Check: Document validity is unexpired.")

    if fingerprint_res.get('status') == 'DOCUMENT_CHANGED':
        raw_risk += 25  # Strong evidence: modified file bytes
        attention_indicators.append("Integrity Alert: File bytes differ from previous submission of this document ID.")
        reasons.append("Document Integrity: Cryptographic hash mismatch against historical entry.")
    elif fingerprint_res.get('status') == 'IDENTICAL_REUPLOAD':
        positive_indicators.append("Document Integrity: Cryptographic hash matches identical previous screening.")

    # -------------------------------------------------------------
    # BOUND & CALIBRATE FINAL RISK SCORE
    # -------------------------------------------------------------
    final_risk_score = min(max(raw_risk, 0), 100)

    # Ensure documents with missing information, OCR uncertainty, or expired validity
    # land squarely in the 26-55 range (Requires Further Verification) if not suspicious
    if (comp_status != 'PASSED' or validation_res.get('is_expired') or ocr_status in ['WARNING', 'NOT VERIFIED']) and final_risk_score < 26:
        final_risk_score = 30

    final_completeness = min(max(verification_completeness, 10), 100)

    # -------------------------------------------------------------
    # CLASSIFICATION TIERS (Exact User Specifications):
    # 0–25: LIKELY GENUINE
    # 26–55: REQUIRES FURTHER VERIFICATION
    # 56+: SUSPICIOUS
    # -------------------------------------------------------------
    if final_risk_score <= 25:
        risk_level = "LOW RISK"
        status_label = "LIKELY GENUINE"
        summary_verdict = "No significant suspicious indicators detected."
        why_this_result = "All required fields were successfully extracted, the document structure was consistent, and no significant alteration or synthetic-document indicators were detected."
        badge_class = "badge-genuine"
        color_code = "#059669"
    elif final_risk_score <= 55:
        risk_level = "MEDIUM RISK"
        status_label = "REQUIRES FURTHER VERIFICATION"
        summary_verdict = "Some inconsistencies or insufficient verification evidence were detected."
        why_this_result = "Some information could not be fully verified or one or more inconsistencies were detected. Further verification is recommended."
        badge_class = "badge-review"
        color_code = "#D97706"
    else:
        risk_level = "HIGH RISK"
        status_label = "SUSPICIOUS"
        summary_verdict = "Multiple suspicious indicators were detected."
        why_this_result = "Multiple suspicious indicators were detected during document structure, consistency, alteration, or synthetic-document screening."
        badge_class = "badge-suspicious"
        color_code = "#DC2626"

    # 7 Security Checks Grid Data (Exact User Specification)
    security_checks = [
        {
            'name': 'OCR Extraction',
            'status': ocr_status,
            'penalty': ocr_penalty,
            'details': ocr_details,
            'icon': 'fa-solid fa-font'
        },
        {
            'name': 'Document Completeness',
            'status': comp_status,
            'penalty': comp_penalty,
            'details': comp_details,
            'icon': 'fa-solid fa-list-check'
        },
        {
            'name': 'Field Consistency',
            'status': cons_status,
            'penalty': cons_penalty,
            'details': cons_details,
            'icon': 'fa-solid fa-arrows-split-up-and-left'
        },
        {
            'name': 'Document Structure',
            'status': struct_status,
            'penalty': struct_penalty,
            'details': struct_details,
            'icon': 'fa-solid fa-shapes'
        },
        {
            'name': 'Alteration Screening',
            'status': vis_status,
            'penalty': vis_penalty,
            'details': vis_details,
            'icon': 'fa-solid fa-microscope'
        },
        {
            'name': 'AI/Synthetic Indicators',
            'status': ai_status,
            'penalty': ai_penalty,
            'details': ai_details,
            'icon': 'fa-solid fa-wand-magic-sparkles'
        },
        {
            'name': 'Database Verification',
            'status': db_status,
            'penalty': db_penalty,
            'details': db_details,
            'icon': 'fa-solid fa-database'
        }
    ]

    # Category risk breakdown
    breakdown = {
        'ocr_quality': min(ocr_penalty, 20),
        'document_completeness': min(comp_penalty, 20),
        'field_consistency': min(cons_penalty, 20),
        'document_structure': min(struct_penalty, 20),
        'visual_alteration': min(vis_penalty, 20),
        'ai_synthetic': min(ai_penalty, 20),
        'database_verification': min(db_penalty, 20),
        'total': final_risk_score
    }

    # Factor contributions list for clean display
    contributing_factors = [
        {'name': 'OCR Quality', 'penalty': ocr_penalty},
        {'name': 'Missing Information', 'penalty': comp_penalty},
        {'name': 'Field Inconsistency', 'penalty': cons_penalty},
        {'name': 'Document Structure', 'penalty': struct_penalty},
        {'name': 'Alteration Indicators', 'penalty': vis_penalty},
        {'name': 'Synthetic Indicators', 'penalty': ai_penalty},
        {'name': 'Database Verification', 'penalty': db_penalty}
    ]

    # Audit Trail Pipeline Steps (Exact User Specification)
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

    return {
        'score': final_risk_score,
        'completeness': final_completeness,
        'risk_level': risk_level,
        'status_label': status_label,
        'summary_verdict': summary_verdict,
        'why_this_result': why_this_result,
        'badge_class': badge_class,
        'color_code': color_code,
        'reasons': reasons if reasons else ["No significant suspicious indicators detected."],
        'positive_indicators': positive_indicators,
        'attention_indicators': attention_indicators,
        'security_checks': security_checks,
        'six_checks': security_checks,  # Alias for backward compatibility
        'breakdown': breakdown,
        'contributing_factors': contributing_factors,
        'audit_trail': audit_trail,
        'checks': validation_res.get('checks', [])
    }
