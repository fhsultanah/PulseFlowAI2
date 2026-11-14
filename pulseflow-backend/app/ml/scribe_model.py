import os
import json
from groq import Groq
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil

# تعريف تطبيق FastAPI مرة واحدة فقط في أعلى الملف
app = FastAPI()

# مفتاح Groq
client = Groq(api_key="API key")

def transcribe_audio(audio_file_path: str) -> str:
    with open(audio_file_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_file_path, file.read()),
            model="whisper-large-v3",
            response_format="text"
        )
    return transcription

def generate(transcript_text: str):
    selected_model = "llama-3.3-70b-versatile"
    
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
    return {
        "soap": result.get("soap_note", {}),
        "icd10": result.get("icd10_suggestions", []),
        "gaps": result.get("compliance_alerts", [])
    }

@app.post("/scribe")
async def scribe_endpoint(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        transcript_text = transcribe_audio(temp_path)
        analysis_result = generate(transcript_text)
        
        return {
            "transcript": transcript_text,
            "soap": analysis_result["soap"],
            "icd10": analysis_result["icd10"],
            "gaps": analysis_result["gaps"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
