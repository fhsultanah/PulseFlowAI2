from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config, db
from .schemas import (AlertOut, ForecastResponse, ScribeRequest, ScribeResponse,
                      SimulateRequest, SimulateResponse, StatusUpdate)
from .services import alerts as alert_svc
from .services import forecast as forecast_svc
from .services import scribe as scribe_svc
from .services import simulate as simulate_svc

app = FastAPI(title="PulseFlow AI API", version="0.1.0",
              description="Prototype API. Synthetic data only, no real patient data.")
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])


def require_key(x_api_key: str | None = Header(default=None)):
    if config.API_KEY and x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")


@app.get("/health")
def health():
    return {"status": "ok", "forecast_mock": config.FORECAST_MOCK, "scribe_mock": config.SCRIBE_MOCK}


@app.get("/forecast", response_model=ForecastResponse)
def forecast(hours: int = Query(12, ge=1, le=24)):
    points, source = forecast_svc.predict(hours)
    return {"generated_at": datetime.now().isoformat(timespec="seconds"),
            "source": source, "threshold": config.SURGE_THRESHOLD, "points": points}


@app.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    return simulate_svc.simulate(req.patients_by_ctas, req.extra_patients, req.available.model_dump())


@app.post("/scribe", response_model=ScribeResponse)
def scribe(req: ScribeRequest):
    result = scribe_svc.generate(req.transcript)
    alert_svc.raise_doc_gap_alert(result["gaps"])
    return result


@app.post("/alerts/check")
def alerts_check(hours: int = Query(12, ge=1, le=24)):
    """Evaluate the forecast and, if needed, raise an alert and push it to n8n.
    Call it from the dashboard demo button or from an n8n Schedule trigger."""
    return alert_svc.check_surge(hours)


@app.get("/alerts", response_model=list[AlertOut])
def alerts_list(limit: int = Query(50, ge=1, le=200)):
    return db.list_alerts(limit)


@app.post("/alerts/{alert_id}/status", dependencies=[Depends(require_key)])
def alert_status(alert_id: int, body: StatusUpdate):
    """n8n calls this after delivering the notification."""
    if not db.set_alert_status(alert_id, body.status):
        raise HTTPException(status_code=404, detail="alert not found")
    return {"id": alert_id, "status": body.status}
