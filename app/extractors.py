from typing import Optional
from pypdf import PdfReader

# OCR imports
try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def extract_pdf_text(path: str) -> Optional[str]:
    try:
        reader = PdfReader(path)
        parts: list[str] = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            if txt:
                parts.append(txt)
        text = "\n".join(parts).strip()
        return text if text else None
    except Exception:
        return None


def extract_image_text(image_path: str) -> Optional[str]:
    """
    Extract text from image using OCR with optional preprocessing.
    Returns None if OCR is not available or extraction fails.
    """
    if not PYTESSERACT_AVAILABLE:
        return None

    try:
        # Load image
        image = Image.open(image_path)

        # Optional preprocessing with OpenCV for better accuracy
        if CV2_AVAILABLE:
            # Convert PIL image to numpy array
            img_array = np.array(image)

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Apply thresholding to improve OCR accuracy
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Convert back to PIL Image
            image = Image.fromarray(thresh)

        # Run OCR
        text = pytesseract.image_to_string(image, lang="eng")

        # Clean up text
        text = text.strip()

        return text if text else None

    except Exception as e:
        # Silently fail - OCR is best-effort
        return None
