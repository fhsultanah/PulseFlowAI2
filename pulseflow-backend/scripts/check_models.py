"""Checks that the real models follow the API contract.

Run from the pulseflow-backend folder (venv active):
    python scripts/check_models.py          # checks app/ml/forecast_model.py and scribe_model.py
    python scripts/check_models.py --mock   # checks the built-in mocks (sanity check)
"""
import importlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ICD = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$")
SAMPLES = [
    "Patient: I have chest pain since morning. I am allergic to penicillin.\n"
    "Doctor: Blood pressure is 130/85, pulse 90. Any current medication?\n"
    "Doctor: We will order an ECG and follow up in the clinic.",
    "المريض: عندي صداع وحرارة من أمس\nالطبيب: نطلب تحليل ونعطيك خافض حرارة",
]


def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check_forecast(points, hours):
    errs = []
    if not isinstance(points, list):
        return [f"predict({hours}) must return a list, got {type(points).__name__}"]
    if len(points) != hours:
        errs.append(f"predict({hours}) returned {len(points)} points, expected {hours}")
    for i, p in enumerate(points):
        if not isinstance(p, dict):
            errs.append(f"point {i} is not a dict")
            continue
        missing = [k for k in ("time", "expected", "lower", "upper") if k not in p]
        if missing:
            errs.append(f"point {i} is missing keys: {missing}")
            continue
        if not isinstance(p["time"], str):
            errs.append(f"point {i}: time must be a string (ISO format)")
        if not all(num(p[k]) for k in ("expected", "lower", "upper")):
            errs.append(f"point {i}: expected/lower/upper must be numbers")
        elif not (0 <= p["lower"] <= p["expected"] <= p["upper"]):
            errs.append(f"point {i}: need 0 <= lower <= expected <= upper, got {p['lower']}, {p['expected']}, {p['upper']}")
    return errs[:8]


def check_scribe(r):
    errs = []
    if not isinstance(r, dict):
        return [f"generate() must return a dict, got {type(r).__name__}"]
    soap = r.get("soap")
    if not isinstance(soap, dict):
        errs.append("'soap' must be a dict")
    else:
        for k in ("subjective", "objective", "assessment", "plan"):
            if not isinstance(soap.get(k), str) or not soap[k].strip():
                errs.append(f"soap.{k} must be a non-empty string (use 'Not documented' if empty)")
    icd = r.get("icd10")
    if not isinstance(icd, list):
        errs.append("'icd10' must be a list")
    else:
        for i, c in enumerate(icd):
            if not isinstance(c, dict) or not all(k in c for k in ("code", "description", "confidence")):
                errs.append(f"icd10[{i}] needs code, description, confidence")
                continue
            if not (isinstance(c["code"], str) and ICD.match(c["code"])):
                errs.append(f"icd10[{i}].code '{c['code']}' does not look like an ICD-10 code")
            if c["confidence"] is not None and not (num(c["confidence"]) and 0 <= c["confidence"] <= 1):
                errs.append(f"icd10[{i}].confidence must be a number between 0 and 1")
    gaps = r.get("gaps")
    if not isinstance(gaps, list):
        errs.append("'gaps' must be a list")
    else:
        for i, g in enumerate(gaps):
            if not isinstance(g, dict) or not all(isinstance(g.get(k), str) for k in ("field", "en", "ar")):
                errs.append(f"gaps[{i}] needs string keys field, en, ar")
    return errs[:8]


def load(module, func, use_mock):
    """Goes through the same service layer the API uses (including normalization)."""
    from app import config
    if module == "forecast_model":
        from app.services import forecast
        config.FORECAST_MOCK = use_mock
        return lambda h: forecast.predict(h)[0]
    from app.services import scribe
    config.SCRIBE_MOCK = use_mock
    if not use_mock:
        try:
            m = importlib.import_module(f"app.ml.{module}")
        except ModuleNotFoundError as e:
            print(f"  FAIL  app/ml/{module}.py not found or missing import: {e}")
            return None
        if not hasattr(m, func):
            print(f"  FAIL  app/ml/{module}.py has no function '{func}'")
            return None
    return scribe.generate


def main():
    use_mock = "--mock" in sys.argv
    failed = False

    print("Forecast (forecast_model.predict)")
    fn = load("forecast_model", "predict", use_mock)
    if fn is None:
        failed = True
    else:
        for h in (1, 12, 24):
            try:
                errs = check_forecast(fn(h), h)
            except Exception as e:
                errs = [f"predict({h}) raised {type(e).__name__}: {e}"]
            print(f"  {'PASS' if not errs else 'FAIL'}  hours={h}")
            for e in errs:
                print("        -", e)
            failed |= bool(errs)

    print("Scribe (scribe_model.generate)")
    fn = load("scribe_model", "generate", use_mock)
    if fn is None:
        failed = True
    else:
        for i, text in enumerate(SAMPLES, 1):
            try:
                out = fn(text)
                errs = check_scribe(out)
                if not errs:
                    if any(c["confidence"] is None for c in out["icd10"]):
                        print("        note: some ICD-10 suggestions have no confidence (null)")
                    if any(not g["ar"] for g in out["gaps"]):
                        print("        note: some gaps have no Arabic text yet")
            except Exception as e:
                errs = [f"generate() raised {type(e).__name__}: {e}"]
            print(f"  {'PASS' if not errs else 'FAIL'}  sample {i}")
            for e in errs:
                print("        -", e)
            failed |= bool(errs)

    print("\nRESULT:", "some checks failed" if failed else "all checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()