"""What-if resource simulation by CTAS level.

IMPORTANT: every number below is a PLACEHOLDER ASSUMPTION, not clinically validated.
Review them with the clinical advisor and cite a source before presenting them as real.
"""
import math

LEVELS = (1, 2, 3, 4, 5)
DEFAULT_MIX = {1: 0.02, 2: 0.13, 3: 0.40, 4: 0.35, 5: 0.10}   # share of extra patients per level
ACUITY_WEIGHT = {1: 4.0, 2: 2.5, 3: 1.5, 4: 1.0, 5: 0.5}      # workload units per patient
LOAD_PER_NURSE = 6.0
LOAD_PER_PHYSICIAN = 12.0

ASSUMPTIONS = (
    "Placeholder acuity weights and staffing ratios; not clinically validated. "
    "To be reviewed with the clinical advisor."
)


def _split_extra(extra):
    counts = {l: int(extra * DEFAULT_MIX[l]) for l in LEVELS}
    left = extra - sum(counts.values())
    order = sorted(LEVELS, key=lambda l: extra * DEFAULT_MIX[l] - counts[l], reverse=True)
    for l in order[:left]:
        counts[l] += 1
    return counts


def simulate(current, extra_patients, available):
    base = {l: int(current.get(l, current.get(str(l), 0))) for l in LEVELS}
    extra = _split_extra(extra_patients)
    counts = {l: base[l] + extra[l] for l in LEVELS}

    load = sum(counts[l] * ACUITY_WEIGHT[l] for l in LEVELS)
    required = {
        "beds": sum(counts.values()),
        "nurses": math.ceil(load / LOAD_PER_NURSE),
        "physicians": math.ceil(load / LOAD_PER_PHYSICIAN),
    }
    avail = {k: int(available[k]) for k in ("beds", "nurses", "physicians")}
    gaps = {k: max(required[k] - avail[k], 0) for k in required}

    pressure = max(required[k] / max(avail[k], 1) for k in required)
    risk = "low" if pressure < 0.8 else "medium" if pressure < 1.0 else "high"

    recs = []
    if gaps["beds"]:
        recs.append({"en": f"Open or free {gaps['beds']} more bed(s).",
                     "ar": f"فتح أو تفريغ {gaps['beds']} سرير إضافي."})
    if gaps["nurses"]:
        recs.append({"en": f"Call in {gaps['nurses']} more nurse(s).",
                     "ar": f"استدعاء {gaps['nurses']} ممرضة/ممرض إضافي."})
    if gaps["physicians"]:
        recs.append({"en": f"Add {gaps['physicians']} physician(s) to the shift.",
                     "ar": f"إضافة {gaps['physicians']} طبيب للمناوبة."})
    if not recs:
        recs.append({"en": "Current resources cover the expected load.",
                     "ar": "الموارد الحالية تغطي الحمل المتوقع."})

    return {
        "patients_by_ctas": counts,
        "required": required,
        "available": avail,
        "gaps": gaps,
        "risk": risk,
        "recommendations": recs,
        "assumptions": ASSUMPTIONS,
    }
