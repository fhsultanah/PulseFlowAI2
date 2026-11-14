"""Alert logic. Backend decides, n8n delivers (self-hosted), n8n reports back status."""
import json
import urllib.request

from .. import config, db
from . import forecast

PATHS = {"surge": "surge", "doc_gap": "doc-gap"}  # n8n Webhook node paths
DEDUP_SECONDS = 30 * 60


def notify_n8n(kind, payload):
    if not config.N8N_WEBHOOK_BASE:
        return "skipped"
    url = f"{config.N8N_WEBHOOK_BASE.rstrip('/')}/{PATHS[kind]}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return "sent" if 200 <= r.status < 300 else "failed"
    except Exception:
        return "failed"


def check_surge(hours=12):
    points, _ = forecast.predict(hours)
    peak = max(points, key=lambda p: p["expected"])
    base = {"threshold": config.SURGE_THRESHOLD, "peak": peak}
    if peak["expected"] < config.SURGE_THRESHOLD:
        return {"triggered": False, "reason": "below_threshold", **base}
    if db.recent_alert_exists("surge", DEDUP_SECONDS):
        return {"triggered": False, "reason": "duplicate_suppressed", **base}
    severity = "high" if peak["expected"] >= config.SURGE_THRESHOLD * 1.25 else "medium"
    message = f"Expected surge: about {peak['expected']} arrivals/hour around {peak['time']}."
    alert = db.add_alert("surge", severity, message, {"peak": peak, "threshold": config.SURGE_THRESHOLD})
    return {"triggered": True, "alert": alert, "delivery": notify_n8n("surge", alert), **base}


def raise_doc_gap_alert(gaps):
    if not gaps:
        return None
    fields = [g["field"] for g in gaps]
    alert = db.add_alert("doc_gap", "medium",
                         "Documentation gaps found: " + ", ".join(fields), {"gaps": fields})
    return {"alert": alert, "delivery": notify_n8n("doc_gap", alert)}
