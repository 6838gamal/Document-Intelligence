import io
import os
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(content: bytes) -> tuple[str, int]:
    """Extract text from PDF bytes. Returns (text, page_count)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        page_count = len(reader.pages)
        pages_text = []
        for page in reader.pages:
            try:
                t = page.extract_text()
                if t:
                    pages_text.append(t.strip())
            except Exception:
                pass
        return "\n\n".join(pages_text), page_count
    except Exception as e:
        logger.error(f"PDF استخراج: {e}")
        return "", 1


def extract_text_from_image_ocr(content: bytes, filename: str = "") -> str:
    """OCR an image using Gemini Vision. Returns extracted text."""
    try:
        import google.generativeai as genai
        import PIL.Image

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning("GEMINI_API_KEY غير مضبوط — تعذّر OCR")
            return ""

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        image = PIL.Image.open(io.BytesIO(content))

        prompt = (
            "استخرج كل النص الموجود في هذه الصورة بدقة عالية. "
            "حافظ على التنسيق والترتيب الأصلي. "
            "إذا كان النص عربياً اكتبه عربياً. "
            "أعطني النص فقط بدون أي شرح."
        )
        response = model.generate_content([prompt, image])
        return response.text.strip()
    except Exception as e:
        logger.error(f"OCR صورة: {e}")
        return ""


def extract_text_from_docx(content: bytes) -> str:
    """Basic DOCX text extraction (no python-docx required)."""
    try:
        import zipfile
        import re
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            with z.open("word/document.xml") as f:
                xml = f.read().decode("utf-8", errors="replace")
        text = re.sub(r"<[^>]+>", " ", xml)
        return " ".join(text.split())
    except Exception as e:
        logger.error(f"DOCX استخراج: {e}")
        return ""


def extract_text(content: bytes, filename: str, content_type: str = "") -> tuple[str, int]:
    """
    Extract text from any supported file.
    Returns (text, page_count).
    """
    fn = filename.lower()

    if fn.endswith(".pdf") or "pdf" in content_type:
        return extract_text_from_pdf(content)

    if any(fn.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"]):
        text = extract_text_from_image_ocr(content, filename)
        return text, 1

    if fn.endswith(".txt"):
        try:
            return content.decode("utf-8", errors="replace"), 1
        except Exception:
            return "", 1

    if fn.endswith(".docx"):
        return extract_text_from_docx(content), 1

    if fn.endswith(".xlsx"):
        try:
            import zipfile, re
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                names = z.namelist()
                texts = []
                for name in names:
                    if name.endswith(".xml"):
                        with z.open(name) as f:
                            xml = f.read().decode("utf-8", errors="replace")
                        texts.append(re.sub(r"<[^>]+>", " ", xml))
            return " ".join(" ".join(t.split()) for t in texts), 1
        except Exception:
            return "", 1

    return "", 1
