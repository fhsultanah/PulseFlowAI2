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


def generate(transcript):
    if not config.SCRIBE_MOCK:
        model = importlib.import_module("app.ml.scribe_model")
        return {**model.generate(transcript), "source": "model"}
    return {**_mock(transcript), "source": "mock"}
