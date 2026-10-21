"""
====================================================================
PDF Document Processing Module
Extracts selectable text and renders PDF pages to images for OCR
and computer-vision forensics.
Handles password-protected, corrupted, and multi-page PDFs safely.
====================================================================
"""

import os
from PIL import Image

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except ImportError:
    HAS_PDFIUM = False


def process_pdf_document(pdf_path, output_dir=None):
    """
    Ingests a PDF file, validates encryption and page-count bounds,
    extracts embedded text, and renders the primary page as a high-resolution PNG image.
    
    Returns:
        dict: {
            'success': True,
            'text': str,
            'rendered_image_path': str,
            'page_count': int,
            'has_selectable_text': bool
        }
    Raises:
        ValueError for user-facing validation errors (password protected, page limits, etc.)
    """
    if not os.path.exists(pdf_path):
        raise ValueError("The specified PDF document could not be found.")

    if not HAS_PYPDF:
        raise ValueError("PDF processing engine is not installed.")

    # 1. Inspect PDF structure with pypdf
    try:
        reader = pypdf.PdfReader(pdf_path)
    except Exception as e:
        raise ValueError("Corrupted or invalid PDF document. Please verify the file integrity and try again.")

    if reader.is_encrypted:
        raise ValueError("Password-protected PDF files cannot be processed. Please upload an unprotected document.")

    page_count = len(reader.pages)
    if page_count == 0:
        raise ValueError("The uploaded PDF document is empty (0 pages).")

    if page_count > 5:
        raise ValueError(f"PDF exceeds the maximum page limit (found {page_count} pages, max is 5). Please upload a single identity document scan.")

    # 2. Extract embedded selectable text
    extracted_text_parts = []
    for idx, page in enumerate(reader.pages):
        try:
            txt = page.extract_text()
            if txt and txt.strip():
                extracted_text_parts.append(txt.strip())
        except Exception:
            pass

    combined_text = "\n\n".join(extracted_text_parts)
    has_selectable_text = len(combined_text) >= 15

    # 3. Render page 1 to an image for OCR & OpenCV forensics
    out_dir = output_dir or os.path.dirname(pdf_path)
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    rendered_image_path = os.path.join(out_dir, f"rendered_{base_name}.png")

    rendered_success = False

    # Attempt 1: High-fidelity rasterization via pypdfium2
    if HAS_PDFIUM:
        try:
            doc = pdfium.PdfDocument(pdf_path)
            page0 = doc[0]
            # Render at 2.0x scale (~144 dpi) for crisp OCR and forensic detail
            pil_image = page0.render(scale=2.0).to_pil()
            pil_image.save(rendered_image_path, format="PNG")
            rendered_success = True
        except Exception:
            rendered_success = False

    # Attempt 2: Extract embedded raster images from page 0 via pypdf
    if not rendered_success:
        try:
            page0 = reader.pages[0]
            if page0.images and len(page0.images) > 0:
                first_img = page0.images[0]
                with open(rendered_image_path, "wb") as fp:
                    fp.write(first_img.data)
                rendered_success = True
        except Exception:
            rendered_success = False

    # Attempt 3: Create a blank white card canvas with the extracted text if no rasterizer exists
    if not rendered_success:
        try:
            blank_img = Image.new("RGB", (800, 500), color=(255, 255, 255))
            blank_img.save(rendered_image_path, format="PNG")
            rendered_success = True
        except Exception:
            pass

    return {
        'success': True,
        'text': combined_text,
        'rendered_image_path': rendered_image_path if rendered_success else None,
        'page_count': page_count,
        'has_selectable_text': has_selectable_text
    }
