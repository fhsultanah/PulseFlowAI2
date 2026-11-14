"""The API contract. Everyone builds against these shapes."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------- /forecast ----------
class ForecastPoint(BaseModel):
    time: str
    expected: float  # expected arrivals per hour
    lower: float
    upper: float


class ForecastResponse(BaseModel):
    generated_at: str
    source: Literal["mock", "model"]
    threshold: int
    points: list[ForecastPoint]


# ---------- /simulate ----------
class Available(BaseModel):
    beds: int = Field(30, ge=0)        # demo defaults, replace with your scenario
    nurses: int = Field(8, ge=0)
    physicians: int = Field(4, ge=0)


class SimulateRequest(BaseModel):
    # current patients per CTAS level (1 = most urgent ... 5 = least)
    patients_by_ctas: dict[int, int] = Field(default_factory=lambda: {1: 1, 2: 3, 3: 8, 4: 6, 5: 2})
    extra_patients: int = Field(0, ge=0, le=200)  # the "what if" slider
    available: Available = Field(default_factory=Available)

    @field_validator("patients_by_ctas")
    @classmethod
    def _check_levels(cls, v):
        for level, n in v.items():
            if level not in (1, 2, 3, 4, 5) or n < 0:
                raise ValueError("CTAS levels must be 1-5 and counts >= 0")
        return v


class Recommendation(BaseModel):
    en: str
    ar: str


class SimulateResponse(BaseModel):
    patients_by_ctas: dict[int, int]
    required: dict[str, int]
    available: dict[str, int]
    gaps: dict[str, int]
    risk: Literal["low", "medium", "high"]
    recommendations: list[Recommendation]
    assumptions: str


# ---------- /scribe ----------
class ScribeRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=20000)  # synthetic text only


class Soap(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class IcdSuggestion(BaseModel):
    code: str
    description: str
    confidence: float


class DocGap(BaseModel):
    field: str
    en: str
    ar: str


class ScribeResponse(BaseModel):
    soap: Soap
    icd10: list[IcdSuggestion]
    gaps: list[DocGap]
    source: Literal["mock", "model"]


# ---------- /alerts ----------
class AlertOut(BaseModel):
    id: int
    kind: str
    severity: str
    message: str
    payload: dict | None = None
    status: str
    created_at: float


class StatusUpdate(BaseModel):
    status: Literal["new", "notified", "acknowledged", "failed"]
