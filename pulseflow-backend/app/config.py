import os

# 1 = use built-in mock logic (works with no model). 0 = use the real module in app/ml/
# Separate switches so each model can go live independently.
FORECAST_MOCK = os.getenv("FORECAST_MOCK", "1") == "1"
SCRIBE_MOCK = os.getenv("SCRIBE_MOCK", "1") == "1"
DB_PATH = os.getenv("DB_PATH", "pulseflow.db")
# n8n webhook base, e.g. http://n8n:5678/webhook  (leave empty to skip notifications)
N8N_WEBHOOK_BASE = os.getenv("N8N_WEBHOOK_BASE", "")
# Expected arrivals per hour above which a surge alert is raised (demo value, tune it)
SURGE_THRESHOLD = int(os.getenv("SURGE_THRESHOLD", "18"))
# Optional: protects the endpoint n8n calls back (header X-API-Key)
API_KEY = os.getenv("API_KEY", "")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
