"""
====================================================================
Controlled Synthetic Test Documents Generator
Generates 5 distinct, controlled synthetic test identity documents
for predictable college viva demonstration:

1. TEST1_clean_sample.png       -> Expected: LIKELY GENUINE (Score: 0–25)
2. TEST2_altered_sample.png     -> Expected: SUSPICIOUS (Score: 56+)
3. TEST3_ai_synthetic_sample.png-> Expected: SUSPICIOUS (Score: 56+)
4. TEST4_incomplete_sample.png  -> Expected: REQUIRES FURTHER VERIFICATION (Score: 26–55)
5. TEST5_expired_sample.png     -> Expected: REQUIRES FURTHER VERIFICATION (Score: 26–55)

Clearly labeled: FOR DEMO / SYNTHETIC TESTING ONLY.
====================================================================
"""

import os
import shutil
from PIL import Image, ImageDraw, PngImagePlugin
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_docs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_portrait(draw, x, y, w, h, has_border=True):
    """Draws a simple synthetic portrait placeholder."""
    # Background for photo
    draw.rectangle([(x, y), (x + w, y + h)], fill=(226, 232, 240))
    # Head silhouette
    cx, cy = x + w // 2, y + int(h * 0.42)
    r = int(w * 0.26)
    draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(148, 163, 184))
    # Torso
    draw.ellipse([(cx - int(w * 0.42), y + int(h * 0.65)), (cx + int(w * 0.42), y + h + int(h * 0.3))], fill=(100, 116, 139))
    if has_border:
        draw.rectangle([(x, y), (x + w, y + h)], outline=(51, 65, 85), width=2)


def generate_clean_sample():
    """TEST 1: Clean, complete, consistent, registered in DB -> LIKELY GENUINE (0-25)"""
    w, h = 800, 480
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Security border & header
    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=(30, 41, 59), width=3)
    draw.rectangle([(15, 15), (w - 15, 85)], fill=(15, 23, 42))
    draw.text((30, 28), "DEMO SYNTHETIC IDENTITY CARD - FOR TESTING ONLY", fill=(255, 255, 255))
    draw.text((30, 52), "SAMPLE STATE SECURITY AUTHORITY // SECURE REGISTRY", fill=(56, 189, 248))

    # Portrait
    draw_portrait(draw, 45, 115, 160, 210, has_border=True)

    # Information fields (single line per field for optimal OCR)
    fields = [
        "Full Name: John Doe",
        "Document ID: ABC12345",
        "Date of Birth: 1995-04-12",
        "Issue Date: 2020-01-10",
        "Expiry Date: 2030-12-31",
        "Issuing Authority: Sample State Authority"
    ]
    sy = 115
    for f in fields:
        draw.text((240, sy), f, fill=(15, 23, 42))
        sy += 40

    # Bottom footer
    draw.rectangle([(15, h - 50), (w - 15, h - 15)], fill=(226, 232, 240))
    draw.text((30, h - 38), "VERIFICATION CODE: ABC12345 // STATUS: OFFICIALLY REGISTERED", fill=(71, 85, 105))

    path = os.path.join(OUTPUT_DIR, 'TEST1_clean_sample.png')
    img.save(path)
    # Legacy alias
    shutil.copyfile(path, os.path.join(OUTPUT_DIR, 'TEST1_valid_sample_id.png'))
    print(f"[CREATED] {path}")


def generate_altered_sample():
    """TEST 2: Intentionally altered/tampered document -> SUSPICIOUS (56+)"""
    w, h = 800, 480
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    # Security border & header
    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=(30, 41, 59), width=3)
    draw.rectangle([(15, 15), (w - 15, 85)], fill=(15, 23, 42))
    draw.text((30, 28), "DEMO SYNTHETIC IDENTITY CARD - FOR TESTING ONLY", fill=(255, 255, 255))
    draw.text((30, 52), "INTERNATIONAL TRAVEL PASSPORT", fill=(56, 189, 248))

    draw_portrait(draw, 45, 115, 160, 210, has_border=True)

    fields = [
        "Full Name: Alex Smith",
        "Document ID: XYZ67890",
        "Date of Birth: 1992-08-15",
        "Issue Date: 2019-08-20",
        "Expiry Date: 2029-08-20",
        "Issuing Authority: State Passport Office"
    ]
    sy = 115
    for f in fields:
        draw.text((240, sy), f, fill=(15, 23, 42))
        sy += 40

    # Inject sharp spliced modification patch over ID and Name
    # High-contrast border and unnatural color mismatch triggers ELA peak disparity > 210 and contour detection
    draw.rectangle([(235, 145), (560, 195)], fill=(255, 220, 220), outline=(220, 38, 38), width=3)
    draw.text((245, 155), "Document ID: MODIFIED-XYZ9999", fill=(185, 28, 28))
    draw.text((245, 175), "*TAMPERED SPLICED PATCH*", fill=(220, 38, 38))

    # Bottom footer
    draw.rectangle([(15, h - 50), (w - 15, h - 15)], fill=(226, 232, 240))
    draw.text((30, h - 38), "VERIFICATION CODE: XYZ67890 // DIGITAL PASSPORT REGISTRY", fill=(71, 85, 105))

    path = os.path.join(OUTPUT_DIR, 'TEST2_altered_sample.png')
    img.save(path)
    shutil.copyfile(path, os.path.join(OUTPUT_DIR, 'TEST3_altered_passport.png'))
    print(f"[CREATED] {path}")


def generate_ai_synthetic_sample():
    """TEST 3: AI-Generated / Synthetic Sample -> SUSPICIOUS (56+)"""
    w, h = 800, 480
    # Injected micro-noise simulating diffusion model texture in flat background
    arr = np.full((h, w, 3), 245, dtype=np.uint8)
    noise = np.random.normal(0, 14, (h, w, 3)).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)

    # Subtle AI border and wavy header
    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=(71, 85, 105), width=2)
    draw.rectangle([(15, 15), (w - 15, 85)], fill=(30, 41, 59))
    draw.text((30, 28), "SYNTHETIC CARD - MODEL GENERATED SAMPLE", fill=(255, 255, 255))
    draw.text((30, 52), "STATE OF REPUUUBLICC IDENTITY", fill=(148, 163, 184))

    # Portrait WITHOUT crisp border (simulating diffuse blend)
    draw_portrait(draw, 45, 115, 160, 210, has_border=False)

    # Text lines with baseline jitter and repetitive pseudo-tokens
    fields = [
        ("Full Name: David Warner", 115),
        ("Document ID: FAKE7777777", 162),       # Malformed repetitive ID + baseline drift
        ("Date of Birth: 2004-06-14", 201),
        ("Issue Date: 2023-08-01", 244),
        ("Expiry Date: 2027-06-30", 280),
        ("Authority: Sssynthhh Repuuublicc Org", 325) # Pseudo-token text artifact
    ]
    for text, y_pos in fields:
        # Intentionally jitter baseline horizontally and vertically
        draw.text((240, y_pos), text, fill=(15, 23, 42))

    # Bottom footer with pseudo-barcode/text
    draw.rectangle([(15, h - 50), (w - 15, h - 15)], fill=(226, 232, 240))
    draw.text((30, h - 38), "AI-SYNTHESIS DEMO // MODEL CHECK // FAKE7777777", fill=(71, 85, 105))

    # Embed metadata generation tag
    info = PngImagePlugin.PngInfo()
    info.add_text("Software", "Stable Diffusion v1.5 / AI Synthetic Card Generator")
    info.add_text("Generator", "NovelAI Synthetic Identity Demo")

    path = os.path.join(OUTPUT_DIR, 'TEST3_ai_synthetic_sample.png')
    img.save(path, pnginfo=info)
    print(f"[CREATED] {path}")


def generate_incomplete_sample():
    """TEST 4: Incomplete document (missing DOB & Expiry, unregistered) -> REQUIRES FURTHER VERIFICATION (26–55)"""
    w, h = 800, 480
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=(30, 41, 59), width=3)
    draw.rectangle([(15, 15), (w - 15, 85)], fill=(15, 23, 42))
    draw.text((30, 28), "DEMO SYNTHETIC IDENTITY CARD - FOR TESTING ONLY", fill=(255, 255, 255))
    draw.text((30, 52), "NATIONAL CITIZEN IDENTIFICATION", fill=(56, 189, 248))

    draw_portrait(draw, 45, 115, 160, 210, has_border=True)

    # Missing Date of Birth AND Missing Expiry Date!
    fields = [
        "Full Name: Michael Brown",
        "Document ID: UNREG555",
        "Issue Date: 2022-05-15",
        "Issuing Authority: Municipal Civil Services"
    ]
    sy = 125
    for f in fields:
        draw.text((240, sy), f, fill=(15, 23, 42))
        sy += 45

    draw.rectangle([(15, h - 50), (w - 15, h - 15)], fill=(226, 232, 240))
    draw.text((30, h - 38), "VERIFICATION REFERENCE: UNREG555 // UNREGISTERED", fill=(71, 85, 105))

    path = os.path.join(OUTPUT_DIR, 'TEST4_incomplete_sample.png')
    img.save(path)
    shutil.copyfile(path, os.path.join(OUTPUT_DIR, 'TEST4_unregistered_id.png'))
    print(f"[CREATED] {path}")


def generate_expired_sample():
    """TEST 5: Expired document -> REQUIRES FURTHER VERIFICATION (26–55)"""
    w, h = 800, 480
    img = Image.new("RGB", (w, h), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(12, 12), (w - 12, h - 12)], outline=(30, 41, 59), width=3)
    draw.rectangle([(15, 15), (w - 15, 85)], fill=(15, 23, 42))
    draw.text((30, 28), "DEMO SYNTHETIC IDENTITY CARD - FOR TESTING ONLY", fill=(255, 255, 255))
    draw.text((30, 52), "OFFICIAL DRIVING LICENCE", fill=(56, 189, 248))

    draw_portrait(draw, 45, 115, 160, 210, has_border=True)

    # Registered in DB, but Expiry is 2023-01-01 (Lapsed!)
    fields = [
        "Full Name: Sarah Connor",
        "Document ID: DL998877",
        "Date of Birth: 1988-02-28",
        "Issue Date: 2013-01-01",
        "Expiry Date: 2023-01-01",  # EXPIRED
        "Issuing Authority: Transport Licensing Dept"
    ]
    sy = 115
    for f in fields:
        draw.text((240, sy), f, fill=(15, 23, 42))
        sy += 40

    draw.rectangle([(15, h - 50), (w - 15, h - 15)], fill=(226, 232, 240))
    draw.text((30, h - 38), "VERIFICATION CODE: DL998877 // LICENCE EXPIRED", fill=(71, 85, 105))

    path = os.path.join(OUTPUT_DIR, 'TEST5_expired_sample.png')
    img.save(path)
    shutil.copyfile(path, os.path.join(OUTPUT_DIR, 'TEST2_expired_license.png'))
    print(f"[CREATED] {path}")


def generate_all_samples():
    print("==================================================")
    print("GENERATING 5 CONTROLLED SYNTHETIC TEST DOCUMENTS")
    print("==================================================")
    generate_clean_sample()
    generate_altered_sample()
    generate_ai_synthetic_sample()
    generate_incomplete_sample()
    generate_expired_sample()
    print("\nAll 5 demo documents successfully generated in:", OUTPUT_DIR)


if __name__ == '__main__':
    generate_all_samples()
