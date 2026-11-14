"""Forecast service.
Jory: put your real model in app/ml/forecast_model.py exposing
    predict(hours: int) -> list[{"time": iso str, "expected": float, "lower": float, "upper": float}]
then run with FORECAST_MOCK=0.
"""
import importlib
import math
import random
from datetime import datetime, timedelta

from .. import config


def _mock(hours):
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    rnd = random.Random(start.strftime("%Y%m%d%H"))
    points = []
    for i in range(1, hours + 1):
        t = start + timedelta(hours=i)
        # synthetic daily pattern: quiet early morning, peak around 18:00
        v = 12 + 7 * math.sin(2 * math.pi * (t.hour - 12) / 24) + rnd.uniform(-1.5, 1.5)
        spread = 1.5 + 0.25 * i
        points.append({
            "time": t.isoformat(timespec="minutes"),
            "expected": round(v, 1),
            "lower": round(max(v - spread, 0), 1),
            "upper": round(v + spread, 1),
        })
    return points


def predict(hours):
    if not config.FORECAST_MOCK:
        model = importlib.import_module("app.ml.forecast_model")
        return model.predict(hours), "model"
    return _mock(hours), "mock"
