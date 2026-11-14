"""Scribe model: SOAP note + ICD-10 suggestions + documentation gaps via Groq.

Needs the env var GROQ_API_KEY (never write the key in code).
Optional: GROQ_MODEL to change the model without editing this file.
NOTE: transcripts are sent to an external API, so use synthetic data only.
"""
import json
import os

from groq import Groq

# Confirm the current model name in the Groq console (Docs > Models).
DEFAULT_MODEL = "openai/gpt-oss-120b"
GAP_FIELDS = ["vitals", "allergies", "medications", "history", "symptom_details", "plan", "other"]

SYSTEM_PROMPT = """You are an emergency-department medical scribe and documentation reviewer.
Read the doctor-patient transcript and return ONE JSON object, nothing else, with exactly these keys:

{
  "soap": {"subjective": "", "objective": "", "assessment": "", "plan": ""},
  "icd10": [{"code": "R07.9", "description": "Chest pain, unspecified"}],
  "gaps": [{"field": "allergies", "en": "Allergies not documented.", "ar": "الحساسية غير موثقة."}]
}

Rules:
- Use only information stated in the transcript. Never invent findings, values or diagnoses.
- If a SOAP section has no information, write "Not documented".
- icd10: suggest only codes supported by what is explicitly documented. Prefer symptom or sign codes
  (for example R07.9 for chest pain). Do not suggest a diagnosis (for example myocardial infarction or
  angina) unless the clinician stated it. Return an empty list if nothing is supported.
  Every code must be a valid ICD-10 code such as R07.9.
- gaps: list each missing critical item separately (vital signs, allergies, current medications,
  relevant history, symptom duration/onset/severity, plan or follow-up).
  "field" must be one of: {FIELDS}. "en" is one short English sentence, "ar" is the same sentence in Arabic.
- Write soap and icd10 descriptions in English.
""".replace("{FIELDS}", ", ".join(GAP_FIELDS))


def _client():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=key, timeout=30.0)


def generate(transcript_text: str):
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    client = _client()
    last_error = None
    for _ in range(2):  # one retry if the model returns invalid JSON
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Transcript:\n{transcript_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        try:
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, dict):
                return {
                    "soap": result.get("soap", {}),
                    "icd10": result.get("icd10", []),
                    "gaps": result.get("gaps", []),
                }
        except (json.JSONDecodeError, TypeError) as e:
            last_error = e
    raise ValueError(f"Model did not return valid JSON: {last_error}")
