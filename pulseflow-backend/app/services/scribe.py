"""Scribe service (SOAP + ICD-10 suggestions + documentation gaps).
Sultana: put your real pipeline in app/ml/scribe_model.py exposing
    generate(transcript: str) -> {"soap": {...}, "icd10": [...], "gaps": [...]}
(same shape as the mock below), then run with SCRIBE_MOCK=0.

The mock is keyword matching only, for the demo flow. Not a real model.
"""
import importlib
import re

from .. import config

ICD_RULES = [
    (("chest pain", "ألم في الصدر", "ألم الصدر"), "R07.9", "Chest pain, unspecified"),
    (("fever", "حمى", "حرارة"), "R50.9", "Fever, unspecified"),
    (("headache", "صداع"), "R51.9", "Headache, unspecified"),
    (("shortness of breath", "ضيق في التنفس", "ضيق نفس"), "R06.02", "Shortness of breath"),
    (("abdominal pain", "ألم في البطن"), "R10.9", "Unspecified abdominal pain"),
    (("cough", "كحة", "سعال"), "R05.9", "Cough, unspecified"),
    (("syncope", "إغماء"), "R55", "Syncope and collapse"),
]

REQUIRED = {
    "allergies": (("allerg", "حساسية"),
                  "Allergies not documented.", "الحساسية غير موثقة."),
    "medications": (("medication", "medicine", "دواء", "أدوية"),
                    "Current medications not documented.", "الأدوية الحالية غير موثقة."),
    "vitals": (("blood pressure", "temperature", "pulse", "spo2", "ضغط الدم", "درجة الحرارة", "نبض", "أكسجين"),
               "Vital signs not documented.", "العلامات الحيوية غير موثقة."),
    "plan": (("plan", "order", "prescribe", "refer", "follow up", "خطة", "نطلب", "نصرف", "نحول", "نحوّل", "متابعة", "تحليل", "أشعة"),
             "Plan not documented.", "خطة العلاج غير موثقة."),
}

_PATIENT = re.compile(r"^\s*(patient|المريض|مريض)\s*[:：]\s*(.*)$", re.I)
_DOCTOR = re.compile(r"^\s*(doctor|dr|الطبيب|طبيب|الدكتور|دكتور)\s*[:：]\s*(.*)$", re.I)


def _has(text, words):
    return any(w in text for w in words)


def _mock(transcript):
    low = transcript.lower()
    patient, doctor = [], []
    for line in transcript.splitlines():
        if m := _PATIENT.match(line):
            patient.append(m.group(2).strip())
        elif m := _DOCTOR.match(line):
            doctor.append(m.group(2).strip())

    objective = [d for d in doctor if _has(d.lower(), REQUIRED["vitals"][0] + ("exam", "فحص"))]
    plan = [d for d in doctor if _has(d.lower(), REQUIRED["plan"][0])]

    icd = [{"code": c, "description": d, "confidence": 0.5}
           for words, c, d in ICD_RULES if _has(low, words)]

    nd = "Not documented"
    soap = {
        "subjective": " ".join(patient) or nd,
        "objective": " ".join(objective) or nd,
        "assessment": "; ".join(i["description"] for i in icd) or nd,
        "plan": " ".join(plan) or nd,
    }
    gaps = [{"field": f, "en": en, "ar": ar}
            for f, (words, en, ar) in REQUIRED.items() if not _has(low, words)]
    return {"soap": soap, "icd10": icd, "gaps": gaps}


GAP_FIELDS = (
    ("vitals", ("vital", "heart rate", "blood pressure", "temperature", "oxygen", "respiratory")),
    ("allergies", ("allerg",)),
    ("medications", ("medication", "drug")),
    ("history", ("history", "risk factor")),
    ("symptom_details", ("duration", "onset", "severity", "character")),
    ("plan", ("plan", "follow-up", "follow up", "management")),
)
SOAP_KEYS = ("subjective", "objective", "assessment", "plan")


def _guess_field(text):
    low = text.lower()
    for field, words in GAP_FIELDS:
        if any(w in low for w in words):
            return field
    return "other"


def normalize(result):
    """Safety net: coerce whatever the model returned into the API contract.
    Never invents values: unknown confidence stays null, missing Arabic stays empty."""
    result = result if isinstance(result, dict) else {}
    raw_soap = result.get("soap") if isinstance(result.get("soap"), dict) else {}
    soap = {k: str(raw_soap.get(k) or "").strip() or "Not documented" for k in SOAP_KEYS}

    icd = []
    for c in result.get("icd10") or []:
        if not isinstance(c, dict) or not str(c.get("code") or "").strip():
            continue
        conf = c.get("confidence")
        ok = isinstance(conf, (int, float)) and not isinstance(conf, bool) and 0 <= conf <= 1
        icd.append({"code": str(c["code"]).strip(),
                    "description": str(c.get("description") or "").strip(),
                    "confidence": float(conf) if ok else None})

    gaps = []
    for g in result.get("gaps") or []:
        if isinstance(g, str) and g.strip():
            gaps.append({"field": _guess_field(g), "en": g.strip(), "ar": ""})
        elif isinstance(g, dict):
            en = str(g.get("en") or g.get("message") or "").strip()
            if en:
                gaps.append({"field": str(g.get("field") or _guess_field(en)),
                             "en": en, "ar": str(g.get("ar") or "")})
    return {"soap": soap, "icd10": icd, "gaps": gaps}


def generate(transcript):
    if not config.SCRIBE_MOCK:
        model = importlib.import_module("app.ml.scribe_model")
        return {**normalize(model.generate(transcript)), "source": "model"}
    return {**_mock(transcript), "source": "mock"}