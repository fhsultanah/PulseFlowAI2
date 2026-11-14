import math
from datetime import datetime, timedelta
import random

def predict(hours: int) -> list[dict]:
    """
    Generates patient volume forecasts for a given number of hours,
    returning the time, expected count, lower bound, and upper bound per system requirements.
    """
    start = datetime.now().replace(minute=0, second=0, microsecond=0)
    rnd = random.Random(start.strftime("%Y%m%d%H"))
    points = []
    
    for i in range(1, hours + 1):
        t = start + timedelta(hours=i)
        # Pattern simulating peak hours and daily volume fluctuations
        v = 12 + 7 * math.sin(2 * math.pi * (t.hour - 12) / 24) + rnd.uniform(-1.5, 1.5)
        spread = 1.5 + 0.25 * i
        
        points.append({
            "time": t.isoformat(timespec="minutes"),
            "expected": round(v, 1),
            "lower": round(max(v - spread, 0), 1),
            "upper": round(v + spread, 1),
        })
        
    return points
