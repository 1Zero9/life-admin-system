from typing import Optional
from pypdf import PdfReader

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
