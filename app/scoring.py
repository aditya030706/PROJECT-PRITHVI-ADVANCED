"""
Compliance Theater Detector -- scoring engine.

Implements the two layers built as real, working logic for this demonstration
(Layer 1: report similarity + static-reading check, Layer 3: sensor
cross-check). Layer 2 (capture-time photo evidence) is intentionally not
implemented here -- per the feature brief's Demonstration Scope, it is an
interface design pending in-app capture, since building trustworthy
server-side timestamp/GPS stamping is outside what this component can
honestly claim to verify on its own.

Design principle carried through every function: nothing here produces an
accusation. Every function returns a *risk contribution*, and only the
combined score, above a stated threshold, results in "flagged_for_review" --
never an automated action against a person or contractor.
"""

from __future__ import annotations
from typing import Optional

from .models import InspectionReport, SensorReading, LayerResult, IntegrityScoreResult
from .similarity import compute_similarity

LAYER1_MAX = 30.0
LAYER3_MAX = 40.0
# Layer 2 max (25.0 in the original 3-layer split shown in the feature brief was
# 30/30/40; since Layer 2 is not implemented here, its weight is excluded from
# the total rather than silently defaulted to zero, so the score returned is
# honestly out of (LAYER1_MAX + LAYER3_MAX) = 70, not out of 100.
MAX_POSSIBLE_SCORE = LAYER1_MAX + LAYER3_MAX

TEXT_SIMILARITY_TRIGGER = 0.85          # cosine similarity above this is "near-identical"
READING_VARIANCE_TRIGGER = 0.02         # absolute variance below this counts as "static"
SENSOR_TOLERANCE_PCT = 0.20             # 20% relative tolerance before flagging mismatch

# NOTE ON THRESHOLD: this is scaled to the two-layer demo total (70 max), not
# the full 100-point design. A supervisor-review flag is raised at 49/70
# (~70% of the achievable demo score) to stay consistent with the "score
# above 70/100" principle stated in the brief. This is an INITIAL, ILLUSTRATIVE
# threshold -- not one calibrated against real inspection archives.
DEMO_THRESHOLD = 0.70 * MAX_POSSIBLE_SCORE  # = 49.0


def _text_similarity(report_a: str, report_b: str) -> tuple[float, str]:
    """Delegates to app.similarity, which tries semantic embeddings first
    and honestly falls back to TF-IDF if the model can't be loaded.
    Returns (similarity, method_used)."""
    return compute_similarity(report_a, report_b)


def _reading_variance(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Absolute difference between two readings. None if either is missing."""
    if current is None or previous is None:
        return None
    return abs(current - previous)


def score_layer1_report_similarity(
    current: InspectionReport, previous: Optional[InspectionReport]
) -> LayerResult:
    """
    Layer 1: flags near-identical report text ONLY when accompanied by
    suspiciously static numeric readings. Identical boilerplate language on
    its own is NOT penalised -- standardised checklist phrasing repeats
    naturally in genuine reports. The risk signal is the *combination* of
    identical language and readings that don't move.
    """
    if previous is None:
        return LayerResult(
            layer="1_report_similarity",
            score=0.0,
            max_score=LAYER1_MAX,
            detail="No prior report available for comparison; layer not applicable.",
        )

    similarity, method_used = _text_similarity(current.report_text, previous.report_text)
    methane_var = _reading_variance(current.methane_pct, previous.methane_pct)
    airflow_var = _reading_variance(current.airflow_m3_min, previous.airflow_m3_min)

    text_flag = similarity >= TEXT_SIMILARITY_TRIGGER
    readings_static = (
        methane_var is not None and methane_var < READING_VARIANCE_TRIGGER
    ) and (
        airflow_var is not None and airflow_var < READING_VARIANCE_TRIGGER
    )

    method_note = (
        "semantic embedding (meaning-based)" if method_used == "semantic_embedding"
        else "TF-IDF word-overlap [FALLBACK: embedding model unavailable]"
    )

    if text_flag and readings_static:
        score = LAYER1_MAX
        detail = (
            f"Text similarity {similarity*100:.1f}% via {method_note} "
            f"(>= {TEXT_SIMILARITY_TRIGGER*100:.0f}% trigger) AND numeric readings static "
            f"(methane Δ={methane_var:.3f}, airflow Δ={airflow_var:.3f}). "
            "Combination indicates possible re-filed report."
        )
    elif text_flag:
        score = 0.0
        detail = (
            f"Text similarity {similarity*100:.1f}% via {method_note} is high, but numeric "
            "readings show natural variance -- consistent with a genuine repeat inspection."
        )
    else:
        score = 0.0
        detail = f"Text similarity {similarity*100:.1f}% via {method_note} -- below trigger threshold."

    return LayerResult(layer="1_report_similarity", score=score, max_score=LAYER1_MAX, detail=detail)


def score_layer3_sensor_crosscheck(
    report: InspectionReport, sensor_reading: Optional[SensorReading]
) -> LayerResult:
    """
    Layer 3: compares the inspector's reported readings against the mine's
    own independent sensor log for the same date. This is the strongest
    layer because it checks against a source the inspector does not control,
    where instrumentation exists.
    """
    if sensor_reading is None or report.methane_pct is None:
        return LayerResult(
            layer="3_sensor_crosscheck",
            score=0.0,
            max_score=LAYER3_MAX,
            detail="No sensor instrumentation available for this mine/date; layer not applicable.",
        )

    methane_diff = abs(report.methane_pct - sensor_reading.methane_pct)
    methane_rel = methane_diff / max(sensor_reading.methane_pct, 1e-6)

    if methane_rel > SENSOR_TOLERANCE_PCT:
        score = LAYER3_MAX
        detail = (
            f"Reported methane {report.methane_pct:.2f}% vs. sensor log "
            f"{sensor_reading.methane_pct:.2f}% -- {methane_rel*100:.0f}% relative mismatch, "
            f"exceeds {SENSOR_TOLERANCE_PCT*100:.0f}% tolerance."
        )
    else:
        score = 0.0
        detail = (
            f"Reported methane {report.methane_pct:.2f}% consistent with sensor log "
            f"{sensor_reading.methane_pct:.2f}% (within tolerance)."
        )

    return LayerResult(layer="3_sensor_crosscheck", score=score, max_score=LAYER3_MAX, detail=detail)


def compute_integrity_score(
    current: InspectionReport,
    previous: Optional[InspectionReport],
    sensor_reading: Optional[SensorReading],
) -> IntegrityScoreResult:
    """Combine implemented layers into a single result. Layer 2 is reported
    as not-implemented so the output is explicit about demonstration scope
    rather than silently treating a missing layer as a passing score."""
    layer1 = score_layer1_report_similarity(current, previous)
    layer2 = LayerResult(
        layer="2_capture_time_evidence",
        score=0.0,
        max_score=0.0,
        detail="Not implemented in this build -- interface design only (see feature brief).",
    )
    layer3 = score_layer3_sensor_crosscheck(current, sensor_reading)

    total = layer1.score + layer3.score
    flagged = total >= DEMO_THRESHOLD

    recommendation = (
        "Route to mine safety supervisor for manual review. No automated action taken."
        if flagged
        else "No action -- file normally."
    )

    return IntegrityScoreResult(
        mine_id=current.mine_id,
        current_report_id=current.report_id,
        previous_report_id=previous.report_id if previous else None,
        layers=[layer1, layer2, layer3],
        total_score=total,
        threshold=DEMO_THRESHOLD,
        flagged_for_review=flagged,
        recommendation=recommendation,
    )
