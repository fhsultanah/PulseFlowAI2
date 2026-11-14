import os
import tempfile
import unittest

from app import config, db
from app.services import alerts, forecast, scribe, simulate


class Base(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        config.DB_PATH = self.path
        config.N8N_WEBHOOK_BASE = ""
        config.FORECAST_MOCK = True
        config.SCRIBE_MOCK = True

    def tearDown(self):
        os.remove(self.path)


class ForecastTests(Base):
    def test_length_and_bounds(self):
        pts, src = forecast.predict(12)
        self.assertEqual(len(pts), 12)
        self.assertEqual(src, "mock")
        for p in pts:
            self.assertLessEqual(p["lower"], p["expected"])
            self.assertLessEqual(p["expected"], p["upper"])


class SimulateTests(Base):
    AV = {"beds": 30, "nurses": 8, "physicians": 4}
    CUR = {1: 1, 2: 3, 3: 8, 4: 6, 5: 2}

    def test_extra_patients_distributed_exactly(self):
        for extra in (0, 1, 7, 20, 53):
            r = simulate.simulate({}, extra, self.AV)
            self.assertEqual(sum(r["patients_by_ctas"].values()), extra)

    def test_more_patients_never_lowers_requirements(self):
        a = simulate.simulate(self.CUR, 0, self.AV)
        b = simulate.simulate(self.CUR, 30, self.AV)
        for k in ("beds", "nurses", "physicians"):
            self.assertGreaterEqual(b["required"][k], a["required"][k])

    def test_big_surge_is_high_risk_with_gaps(self):
        r = simulate.simulate(self.CUR, 40, self.AV)
        self.assertEqual(r["risk"], "high")
        self.assertGreater(r["gaps"]["beds"], 0)


class ScribeTests(Base):
    FULL = ("Patient: I have chest pain since morning. I am allergic to penicillin.\n"
            "Doctor: Blood pressure is 130/85, pulse 90. Any current medication?\n"
            "Doctor: We will order an ECG and follow up in the clinic.")
    ARABIC = ("المريض: عندي صداع وحرارة من أمس\n"
              "الطبيب: نطلب تحليل ونعطيك خافض حرارة")

    def test_full_note_has_no_gaps(self):
        r = scribe.generate(self.FULL)
        self.assertEqual(r["gaps"], [])
        self.assertIn("R07.9", [i["code"] for i in r["icd10"]])

    def test_arabic_detection_and_gaps(self):
        r = scribe.generate(self.ARABIC)
        codes = [i["code"] for i in r["icd10"]]
        self.assertIn("R51.9", codes)
        self.assertIn("R50.9", codes)
        fields = [g["field"] for g in r["gaps"]]
        self.assertIn("allergies", fields)
        self.assertIn("vitals", fields)
        self.assertNotIn("plan", fields)


class AlertTests(Base):
    def test_below_threshold_no_alert(self):
        config.SURGE_THRESHOLD = 999
        self.assertFalse(alerts.check_surge()["triggered"])
        self.assertEqual(db.list_alerts(), [])

    def test_trigger_then_dedup(self):
        config.SURGE_THRESHOLD = 0
        first = alerts.check_surge()
        self.assertTrue(first["triggered"])
        self.assertEqual(first["delivery"], "skipped")
        second = alerts.check_surge()
        self.assertFalse(second["triggered"])
        self.assertEqual(second["reason"], "duplicate_suppressed")
        self.assertEqual(len(db.list_alerts()), 1)

    def test_doc_gap_alert_and_status_update(self):
        res = alerts.raise_doc_gap_alert([{"field": "vitals", "en": "", "ar": ""}])
        aid = res["alert"]["id"]
        self.assertTrue(db.set_alert_status(aid, "notified"))
        self.assertEqual(db.list_alerts()[0]["status"], "notified")
        self.assertFalse(db.set_alert_status(9999, "notified"))
        self.assertIsNone(alerts.raise_doc_gap_alert([]))


if __name__ == "__main__":
    unittest.main()
