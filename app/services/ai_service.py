import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-1.5-flash"

DOCUMENT_TYPES = [
    "فاتورة", "عقد", "تقرير", "مخطط", "مواصفات فنية",
    "سياسة", "عرض أسعار", "محضر اجتماع", "بطاقة هوية",
    "جواز سفر", "كشف حساب بنكي", "أمر شراء", "نموذج موارد بشرية",
    "وثيقة قانونية", "وثيقة طبية", "وثيقة لوجستية", "أخرى",
]

EXTRACTION_SCHEMAS = {
    "فاتورة":         ["رقم الفاتورة", "التاريخ", "اسم المورد", "المبلغ الإجمالي", "الضريبة", "تاريخ الاستحقاق", "العملة"],
    "عقد":            ["أطراف العقد", "تاريخ البداية", "تاريخ النهاية", "قيمة العقد", "موضوع العقد", "بند الفسخ"],
    "أمر شراء":       ["رقم الأمر", "المورد", "التاريخ", "الإجمالي", "البنود", "شروط الدفع"],
    "كشف حساب بنكي": ["اسم الحساب", "رقم الحساب", "الفترة", "الرصيد الافتتاحي", "الرصيد الختامي", "إجمالي الإيرادات", "إجمالي المصروفات"],
    "تقرير":          ["عنوان التقرير", "التاريخ", "المؤلف", "الملخص التنفيذي", "النتائج الرئيسية", "التوصيات"],
    "عرض أسعار":      ["رقم العرض", "مقدم العرض", "التاريخ", "صلاحية العرض", "الإجمالي", "بنود العرض"],
    "بطاقة هوية":     ["الاسم الكامل", "رقم الهوية", "تاريخ الميلاد", "تاريخ الإصدار", "تاريخ الانتهاء", "الجنسية"],
    "جواز سفر":       ["الاسم الكامل", "رقم الجواز", "الجنسية", "تاريخ الميلاد", "تاريخ الإصدار", "تاريخ الانتهاء"],
    "وثيقة طبية":     ["اسم المريض", "التاريخ", "الطبيب المعالج", "التشخيص", "العلاج الموصوف", "الملاحظات"],
}


def _get_model():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY غير مضبوط")
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(MODEL_NAME)


def _clean_json(text: str) -> str:
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


def classify_document(text: str, title: str = "") -> dict:
    try:
        model = _get_model()
        types_list = "\n".join(f"- {t}" for t in DOCUMENT_TYPES)
        prompt = f"""أنت خبير تصنيف مستندات. صنّف المستند التالي وأجب بـ JSON فقط.

عنوان المستند: {title}
نص المستند (أول 2000 حرف):
{text[:2000]}

الأنواع المتاحة:
{types_list}

JSON المطلوب:
{{
  "type": "النوع من القائمة",
  "confidence": رقم_0_إلى_100,
  "reasoning": "سبب التصنيف"
}}"""
        response = model.generate_content(prompt)
        return json.loads(_clean_json(response.text))
    except Exception as e:
        logger.error(f"تصنيف: {e}")
        return {"type": "أخرى", "confidence": 0, "reasoning": "فشل التصنيف"}


def extract_fields(text: str, doc_type: str) -> dict:
    try:
        model = _get_model()
        fields = EXTRACTION_SCHEMAS.get(doc_type, ["التاريخ", "الموضوع", "الأطراف المعنية", "المبلغ إن وُجد", "الجهة المُصدِرة"])
        fields_list = "\n".join(f"- {f}" for f in fields)
        prompt = f"""أنت خبير استخراج بيانات. استخرج الحقول التالية من نص المستند.

نوع المستند: {doc_type}
الحقول المطلوبة:
{fields_list}

نص المستند:
{text[:3500]}

أجب بـ JSON فقط — المفاتيح هي أسماء الحقول، القيم هي البيانات المستخرجة (أو "غير متوفر")."""
        response = model.generate_content(prompt)
        return json.loads(_clean_json(response.text))
    except Exception as e:
        logger.error(f"استخراج: {e}")
        return {}


def generate_summary(text: str, title: str = "") -> str:
    try:
        model = _get_model()
        prompt = f"""اكتب ملخصاً تنفيذياً احترافياً باللغة العربية في 4-6 جمل لهذا المستند.
تضمن: الموضوع الرئيسي، الأطراف المعنية، الأرقام أو التواريخ المهمة، والاستنتاجات.

العنوان: {title}
النص:
{text[:3000]}

الملخص:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"ملخص: {e}")
        return ""


def answer_question(text: str, question: str, doc_title: str = "") -> str:
    try:
        model = _get_model()
        prompt = f"""أنت مساعد ذكي لتحليل المستندات. أجب على السؤال بناءً على المستند فقط.

المستند: {doc_title}
المحتوى:
{text[:4000]}

السؤال: {question}

تعليمات:
- استند فقط إلى المعلومات الموجودة في المستند
- إن لم تجد إجابة واضحة فقل ذلك صراحةً
- أجب بإيجاز ودقة باللغة العربية
- اذكر الأرقام والتواريخ بدقة

الإجابة:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"سؤال وجواب: {e}")
        return "عذراً، لم أتمكن من معالجة هذا السؤال."


def detect_fraud_indicators(text: str, extracted_data: dict) -> dict:
    try:
        model = _get_model()
        data_str = json.dumps(extracted_data, ensure_ascii=False, indent=2)
        prompt = f"""أنت خبير كشف احتيال في المستندات. راجع البيانات وحدد أي مؤشرات مشبوهة.

البيانات المستخرجة:
{data_str}

نص المستند:
{text[:2000]}

أجب بـ JSON فقط:
{{
  "risk_level": "low|medium|high",
  "indicators": ["المؤشرات المشبوهة إن وُجدت"],
  "notes": "ملاحظات عامة"
}}"""
        response = model.generate_content(prompt)
        return json.loads(_clean_json(response.text))
    except Exception as e:
        logger.error(f"كشف احتيال: {e}")
        return {"risk_level": "unknown", "indicators": [], "notes": ""}


def process_document_pipeline(text: str, title: str, filename: str) -> dict:
    """
    Run the full AI pipeline: classify → extract → summarize.
    Returns a dict with all results.
    """
    if not text or not text.strip():
        return {
            "classification": {"type": "أخرى", "confidence": 0, "reasoning": "لا يوجد نص"},
            "extracted_fields": {},
            "summary": "",
            "fraud": {"risk_level": "unknown", "indicators": [], "notes": ""},
        }

    classification = classify_document(text, title)
    doc_type = classification.get("type", "أخرى")
    extracted = extract_fields(text, doc_type)
    summary = generate_summary(text, title)
    fraud = detect_fraud_indicators(text, extracted)

    return {
        "classification": classification,
        "extracted_fields": extracted,
        "summary": summary,
        "fraud": fraud,
    }
