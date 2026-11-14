import os
import json
from groq import Groq

# تهيئة عميل Groq باستخدام مفتاحك الموجود
client = Groq(api_key="API key")

def generate(transcript_text: str):
    # جلب الموديلات المتاحة واختيار الموديل المناسب
    models = client.models.list()
    available_models = [
        m.id for m in models.data 
        if "whisper" not in m.id and "guard" not in m.id and "tts" not in m.id
    ]
    selected_model = available_models[0]

    system_prompt = """
    You are an expert emergency medical scribe and compliance officer. 
    Analyze the transcript and return a JSON object with the following keys:
    1. "soap_note": {
    "subjective": "...",
    "objective": "...",
    "assessment": "...",
    "plan": "..."
    }
    2. "icd10_suggestions": [
        {"code": "...", "description": "..."}
    ]
    3. "compliance_alerts": [
        "List any missing critical information (e.g., vital signs, duration of symptoms, allergies) or empty fields."
    ]
    """
    
    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{transcript_text}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    result = json.loads(response.choices[0].message.content)
    
    # إرجاع النتيجة بالشكل اللي طلبته وجد تماماً (مع المسميات المطلوبة)
    return {
        "soap": result.get("soap_note", {}),
        "icd10": result.get("icd10_suggestions", []),
        "gaps": result.get("compliance_alerts", [])
    }