"""Scribe model via Groq: speech-to-text, then SOAP note + ICD-10 suggestions + documentation gaps.

Needs the env var GROQ_API_KEY (never write the key in code).
Optional: GROQ_MODEL (text model) and GROQ_STT_MODEL (speech model).
NOTE: audio and transcripts are sent to an external API, so use synthetic data only.
"""
import json
import os

from groq import Groq

# Tried in order; the first one that works is used. Confirm names in the Groq console (Docs > Models).
TEXT_MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"]
STT_MODEL = "whisper-large-v3"
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


def transcribe(filename: str, data: bytes) -> str:
    """Audio bytes -> text (Whisper on Groq)."""
    result = _client().audio.transcriptions.create(
        file=(filename, data),
        model=os.environ.get("GROQ_STT_MODEL", STT_MODEL),
        response_format="text",
    )
    return result if isinstance(result, str) else getattr(result, "text", str(result))


def _models():
    chosen = os.environ.get("GROQ_MODEL")
    return [chosen] + [m for m in TEXT_MODELS if m != chosen] if chosen else TEXT_MODELS


def generate(transcript_text: str):
    client = _client()
    last_error = None
    for model in _models():
        for _ in range(2):  # one retry if the model returns invalid JSON
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Transcript:\n{transcript_text}"},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                result = json.loads(response.choices[0].message.content)
                if isinstance(result, dict):
                    return {
                        "soap": result.get("soap", {}),
                        "icd10": result.get("icd10", []),
                        "gaps": result.get("gaps", []),
                    }
            except (json.JSONDecodeError, TypeError) as e:
                last_error = e            # bad JSON: retry the same model once
            except Exception as e:
                last_error = e
                if getattr(e, "status_code", None) in (400, 404):
                    break                  # model unavailable or unsupported: try the next one
                raise                      # auth, network, rate limit: surface the real error
    raise ValueError(f"No model returned a valid answer: {last_error}")