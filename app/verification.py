"""
PRITHVI — Verification Engine v1
=================================

Purpose
-------

Verify a submitted mine inspection using multiple independent
sources of evidence.

Core principle
--------------

ONE BAD SENSOR MUST NOT FLAG THE INSPECTION.

The engine therefore separates:

    source anomaly
        from
    evidence conflict
        from
    report-level verification failure

A single unreliable sensor becomes a SOURCE_ANOMALY signal.

It does not automatically become:

    REINSPECTION_RECOMMENDED
    or
    HUMAN REVIEW REQUIRED

unless independent evidence supports the concern.

Verification is explainable and deterministic in v1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median
from uuid import uuid4

from . import database as db

from .models import (
    InspectionStatus,
    VerificationStatus,
    VerificationResult,
    VerificationSignal,
)

from .document_ai import (
    DOCUMENT_ROOT,
    extract_pdf_text,
    extract_numeric_readings,
    sha256_file,
)

from .similarity import compute_similarity


# ============================================================
# CONFIGURATION
# ============================================================

# Sensor readings are considered temporally comparable to a
# field measurement if they are within this window.
SENSOR_TIME_WINDOW_MINUTES = 15

# Relative difference used for source disagreement.
# Example:
#
# manual = 1.00
# sensor = 1.20
#
# difference = 20%
#
# -> disagreement.
RELATIVE_DISAGREEMENT_THRESHOLD = 0.15

# A very small value avoids division by zero.
EPSILON = 1e-9


# ============================================================
# HELPERS
# ============================================================

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value)

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def _relative_difference(
    a: float,
    b: float,
) -> float:

    denominator = max(
        abs(a),
        abs(b),
        EPSILON,
    )

    return abs(a - b) / denominator


def _same_measurement_type(
    a: str,
    b: str,
) -> bool:

    return (
        a.strip().lower()
        == b.strip().lower()
    )


# ============================================================
# DATA RETRIEVAL
# ============================================================

def _get_inspection_data(
    inspection_id: str,
) -> dict:

    conn = db._connect()

    inspection = conn.execute(
        """
        SELECT *
        FROM inspections
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchone()

    if inspection is None:
        conn.close()

        raise ValueError(
            "Inspection not found."
        )

    measurements = conn.execute(
        """
        SELECT *
        FROM measurements
        WHERE inspection_id = ?
        ORDER BY captured_at
        """,
        (inspection_id,),
    ).fetchall()

    checklist = conn.execute(
        """
        SELECT *
        FROM checklist_results
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    evidence = conn.execute(
        """
        SELECT *
        FROM evidence
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    findings = conn.execute(
        """
        SELECT *
        FROM findings
        WHERE inspection_id = ?
        """,
        (inspection_id,),
    ).fetchall()

    conn.close()

    return {
        "inspection": dict(inspection),
        "measurements": [
            dict(row)
            for row in measurements
        ],
        "checklist": [
            dict(row)
            for row in checklist
        ],
        "evidence": [
            dict(row)
            for row in evidence
        ],
        "findings": [
            dict(row)
            for row in findings
        ],
    }


def _get_sensor_sources(
    mine_id: str,
    measurement_type: str,
    captured_at: datetime | None,
) -> list[dict]:

    conn = db._connect()

    rows = conn.execute(
        """
        SELECT
            sr.*,
            s.reliability_score,
            s.calibration_status,
            s.active
        FROM sensor_readings sr
        JOIN sensors s
            ON sr.sensor_id = s.sensor_id
        WHERE sr.mine_id = ?
          AND sr.measurement_type = ?
          AND s.active = 1
        ORDER BY sr.reading_time DESC
        """,
        (
            mine_id,
            measurement_type,
        ),
    ).fetchall()

    conn.close()

    if captured_at is None:
        return [
            dict(row)
            for row in rows
        ]

    comparable = []

    for row in rows:

        reading_time = _parse_datetime(
            row["reading_time"]
        )

        if reading_time is None:
            continue

        difference = abs(
            (
                captured_at
                - reading_time
            ).total_seconds()
        )

        if (
            difference
            <= SENSOR_TIME_WINDOW_MINUTES * 60
        ):
            comparable.append(
                dict(row)
            )

    return comparable


# ============================================================
# SIGNAL FACTORY
# ============================================================

def _signal(
    inspection_id: str,
    category: str,
    name: str,
    status: str,
    severity: str,
    explanation: str,
    score: float | None = None,
) -> VerificationSignal:

    return VerificationSignal(
        signal_id=(
            f"SIG-"
            f"{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        category=category,
        name=name,
        status=status,
        severity=severity,
        score=score,
        explanation=explanation,
    )


# ============================================================
# MEASUREMENT VERIFICATION
# ============================================================

def _verify_measurements(
    inspection_id: str,
    mine_id: str,
    measurements: list[dict],
) -> tuple[
    list[VerificationSignal],
    list[str],
    list[str],
]:

    signals = []
    source_anomalies = []
    conflicts = []

    if not measurements:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="measurement",
                name="Measurement availability",
                status="insufficient_evidence",
                severity="warning",
                score=0.0,
                explanation=(
                    "No structured field measurements "
                    "were submitted. Sensor consensus cannot "
                    "be evaluated for this inspection."
                ),
            )
        )

        return (
            signals,
            source_anomalies,
            conflicts,
        )

    for measurement in measurements:

        measurement_type = (
            measurement["measurement_type"]
        )

        manual_value = float(
            measurement["value"]
        )

        captured_at = _parse_datetime(
            measurement["captured_at"]
        )

        sensors = _get_sensor_sources(
            mine_id,
            measurement_type,
            captured_at,
        )

        # ----------------------------------------------------
        # No comparable sensor
        # ----------------------------------------------------

        if not sensors:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="measurement",
                    name=(
                        f"{measurement_type} "
                        "source availability"
                    ),
                    status="no_independent_source",
                    severity="info",
                    score=None,
                    explanation=(
                        f"No comparable registered sensor "
                        f"reading was available for "
                        f"{measurement_type}. The field value "
                        f"is retained but cannot be independently "
                        f"cross-checked."
                    ),
                )
            )

            continue

        # ----------------------------------------------------
        # Sensor values
        # ----------------------------------------------------

        sensor_values = [
            float(row["value"])
            for row in sensors
        ]

        sensor_median = median(
            sensor_values
        )

        difference = _relative_difference(
            manual_value,
            sensor_median,
        )

        # ----------------------------------------------------
        # Source reliability
        # ----------------------------------------------------

        reliable_sensors = [
            row
            for row in sensors
            if float(
                row["reliability_score"]
            ) >= 0.70
        ]

        # ----------------------------------------------------
        # Agreement
        # ----------------------------------------------------

        if (
            difference
            <= RELATIVE_DISAGREEMENT_THRESHOLD
        ):

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="measurement_consistency",
                    name=(
                        f"{measurement_type} "
                        "cross-source consistency"
                    ),
                    status="consistent",
                    severity="info",
                    score=1.0,
                    explanation=(
                        f"Field reading {manual_value} "
                        f"is consistent with the sensor "
                        f"consensus median {sensor_median:.4f}."
                    ),
                )
            )

            continue

        # ----------------------------------------------------
        # Sensor disagreement
        # ----------------------------------------------------

        sensor_spread = max(
            sensor_values
        ) - min(
            sensor_values
        )

        sensor_relative_spread = (
            sensor_spread
            / max(
                abs(sensor_median),
                EPSILON,
            )
        )

        # ----------------------------------------------------
        # CASE A:
        # one sensor is the outlier but the other sensors agree.
        #
        # THIS IS THE CRITICAL FAULT-TOLERANT PATH.
        # ----------------------------------------------------

        if len(sensors) >= 3:

            deviations = [
                _relative_difference(
                    value,
                    sensor_median,
                )
                for value in sensor_values
            ]

            extreme_count = sum(
                deviation
                > RELATIVE_DISAGREEMENT_THRESHOLD
                for deviation in deviations
            )

            if extreme_count == 1:

                outlier_index = next(
                    index
                    for index, deviation
                    in enumerate(deviations)
                    if deviation
                    > RELATIVE_DISAGREEMENT_THRESHOLD
                )

                outlier_sensor = sensors[
                    outlier_index
                ]

                source_id = (
                    outlier_sensor["sensor_id"]
                )

                source_anomalies.append(
                    source_id
                )

                signals.append(
                    _signal(
                        inspection_id=inspection_id,
                        category="source_reliability",
                        name=(
                            f"Sensor anomaly — "
                            f"{measurement_type}"
                        ),
                        status="source_anomaly",
                        severity="warning",
                        score=0.35,
                        explanation=(
                            f"Sensor {source_id} disagrees "
                            f"with the multi-sensor consensus. "
                            f"The other sources remain mutually "
                            f"consistent. This source is isolated "
                            f"as an anomaly rather than allowing "
                            f"one faulty machine to flag the "
                            f"inspection."
                        ),
                    )
                )

                continue

        # ----------------------------------------------------
        # CASE B:
        # only one sensor.
        #
        # Do NOT declare fraud or inspection failure.
        # ----------------------------------------------------

        if len(sensors) == 1:

            source_id = sensors[0][
                "sensor_id"
            ]

            source_anomalies.append(
                source_id
            )

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="source_reliability",
                    name=(
                        f"Single-source disagreement — "
                        f"{measurement_type}"
                    ),
                    status="source_anomaly",
                    severity="warning",
                    score=0.30,
                    explanation=(
                        f"The field reading {manual_value} "
                        f"differs from sensor {source_id} "
                        f"reading {sensor_median:.4f}. "
                        f"Because only one independent sensor "
                        f"source is available, PRITHVI does not "
                        f"treat this as sufficient evidence to "
                        f"flag the inspection."
                    ),
                )
            )

            continue

        # ----------------------------------------------------
        # CASE C:
        # multiple sources disagree.
        # ----------------------------------------------------

        if len(reliable_sensors) >= 2:

            conflicts.append(
                (
                    f"{measurement_type}: field value "
                    f"{manual_value} differs from sensor "
                    f"consensus {sensor_median:.4f} "
                    f"by {difference * 100:.1f}%"
                )
            )

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="evidence_conflict",
                    name=(
                        f"{measurement_type} "
                        "multi-source conflict"
                    ),
                    status="conflict",
                    severity="high",
                    score=0.85,
                    explanation=(
                        f"Multiple independent sensor sources "
                        f"support a value materially different "
                        f"from the field reading. This is a "
                        f"report-level evidence conflict and "
                        f"requires human review."
                    ),
                )
            )

        else:

            source_anomalies.extend(
                row["sensor_id"]
                for row in sensors
            )

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="source_reliability",
                    name=(
                        f"{measurement_type} "
                        "low-confidence sensor evidence"
                    ),
                    status="source_anomaly",
                    severity="warning",
                    score=0.30,
                    explanation=(
                        "Available sensor sources disagree, "
                        "but the available source reliability "
                        "is insufficient to establish a "
                        "report-level conflict."
                    ),
                )
            )

    return (
        signals,
        list(dict.fromkeys(source_anomalies)),
        conflicts,
    )


# ============================================================
# STATUTORY THRESHOLD VERIFICATION
# ============================================================

def _verify_thresholds(
    inspection_id: str,
    template_id: Optional[str],
    measurements: list[dict],
) -> list[VerificationSignal]:
    """
    Evaluate field measurements against statutory template threshold limits.
    A threshold violation becomes an explainable VerificationSignal.
    A threshold violation does NOT block submission.
    """
    if not measurements or not template_id:
        return []

    tmpl = db.get_inspection_template(template_id)
    if not tmpl or not tmpl.measurements:
        return []

    # Map template measurement definitions
    threshold_map: dict[str, Any] = {}
    for tm in tmpl.measurements:
        if tm.min_value is not None or tm.max_value is not None:
            threshold_map[tm.measurement_id.lower()] = tm
            threshold_map[tm.name.lower()] = tm

    signals: list[VerificationSignal] = []

    for m in measurements:
        raw_type = (m.get("measurement_type") or "").strip()
        type_lower = raw_type.lower()
        try:
            val = float(m.get("value"))
        except (TypeError, ValueError):
            continue

        defn = threshold_map.get(type_lower)
        if not defn:
            for cand_key, cand_tm in threshold_map.items():
                if cand_key in type_lower or type_lower in cand_key:
                    defn = cand_tm
                    break

        if not defn:
            continue

        is_ch4 = "methane" in defn.name.lower() or "ch4" in defn.name.lower()
        unit_str = defn.unit or m.get("unit") or ""
        thresh_label = defn.threshold_label or ""

        if defn.max_value is not None and val > defn.max_value:
            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="regulatory_threshold",
                    name=f"Threshold: {defn.name}",
                    status="threshold_exceeded",
                    severity="critical" if is_ch4 else "warning",
                    score=0.0,
                    explanation=(
                        f"Field measurement for {defn.name} ({val} {unit_str}) exceeds "
                        f"statutory maximum threshold of {defn.max_value} {unit_str} ({thresh_label})."
                    ),
                )
            )
        elif defn.min_value is not None and val < defn.min_value:
            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="regulatory_threshold",
                    name=f"Threshold: {defn.name}",
                    status="threshold_below_minimum",
                    severity="warning",
                    score=0.0,
                    explanation=(
                        f"Field measurement for {defn.name} ({val} {unit_str}) is below "
                        f"statutory minimum threshold of {defn.min_value} {unit_str} ({thresh_label})."
                    ),
                )
            )
        else:
            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="regulatory_threshold",
                    name=f"Threshold: {defn.name}",
                    status="compliant",
                    severity="info",
                    score=1.0,
                    explanation=(
                        f"Field measurement for {defn.name} ({val} {unit_str}) conforms "
                        f"to statutory threshold limits ({thresh_label})."
                    ),
                )
            )

    return signals


# ============================================================
# CHECKLIST VERIFICATION
# ============================================================

def _verify_checklist(
    inspection_id: str,
    checklist: list[dict],
) -> tuple[
    list[VerificationSignal],
    list[str],
]:

    signals = []
    conflicts = []

    if not checklist:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="completeness",
                name="Checklist completeness",
                status="insufficient_evidence",
                severity="warning",
                score=0.0,
                explanation=(
                    "No checklist results were submitted."
                ),
            )
        )

        return signals, conflicts

    failed = [
        item
        for item in checklist
        if not bool(item["passed"])
    ]

    if not failed:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="checklist",
                name="Checklist consistency",
                status="passed",
                severity="info",
                score=1.0,
                explanation=(
                    "All submitted checklist items "
                    "were marked as passed."
                ),
            )
        )

        return signals, conflicts

    severe_failures = [
        item
        for item in failed
        if (
            item.get("observation")
            and len(
                str(
                    item["observation"]
                ).strip()
            ) > 0
        )
    ]

    signals.append(
        _signal(
            inspection_id=inspection_id,
            category="checklist",
            name="Checklist findings",
            status="failed_items",
            severity="high",
            score=0.85,
            explanation=(
                f"{len(failed)} checklist item(s) "
                f"were marked as failed."
            ),
        )
    )

    if severe_failures:

        conflicts.append(
            (
                f"{len(severe_failures)} failed checklist "
                "item(s) contain recorded observations."
            )
        )

    return signals, conflicts


# ============================================================
# EVIDENCE VERIFICATION
# ============================================================

def _verify_evidence(
    inspection_id: str,
    evidence: list[dict],
) -> tuple[
    list[VerificationSignal],
    list[str],
]:

    signals = []
    conflicts = []

    if not evidence:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="evidence",
                name="Evidence availability",
                status="insufficient_evidence",
                severity="warning",
                score=0.0,
                explanation=(
                    "No supporting evidence was attached "
                    "to the inspection."
                ),
            )
        )

        return signals, conflicts

    # --------------------------------------------------------
    # Duplicate cryptographic hashes
    # --------------------------------------------------------

    hashes = {}

    for item in evidence:

        sha = item.get("sha256")

        if sha:

            hashes.setdefault(
                sha,
                [],
            ).append(
                item["evidence_id"]
            )

    duplicates = {
        sha: ids
        for sha, ids in hashes.items()
        if len(ids) > 1
    }

    if duplicates:

        for sha, ids in duplicates.items():

            conflicts.append(
                (
                    "Duplicate evidence hash detected: "
                    f"{sha[:16]}..."
                )
            )

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="evidence_integrity",
                    name="Duplicate evidence",
                    status="duplicate",
                    severity="high",
                    score=0.90,
                    explanation=(
                        f"The same SHA-256 evidence hash "
                        f"appears in {len(ids)} evidence "
                        f"records."
                    ),
                )
            )

    else:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="evidence_integrity",
                name="Evidence uniqueness",
                status="no_duplicate_detected",
                severity="info",
                score=1.0,
                explanation=(
                    "No duplicate SHA-256 evidence hash "
                    "was detected within this inspection."
                ),
            )
        )

    # --------------------------------------------------------
    # Metadata verification
    # --------------------------------------------------------

    verified_metadata = sum(
        bool(
            item["metadata_verified"]
        )
        for item in evidence
    )

    signals.append(
        _signal(
            inspection_id=inspection_id,
            category="evidence_metadata",
            name="Evidence metadata",
            status=(
                "verified"
                if verified_metadata
                else "not_verified"
            ),
            severity=(
                "info"
                if verified_metadata
                else "warning"
            ),
            score=(
                verified_metadata
                / max(len(evidence), 1)
            ),
            explanation=(
                f"{verified_metadata} of "
                f"{len(evidence)} evidence item(s) "
                f"have verified metadata."
            ),
        )
    )

    return signals, conflicts


# ============================================================
# GPS VERIFICATION
# ============================================================

def _verify_gps(
    inspection_id: str,
    inspection: dict,
) -> list[VerificationSignal]:

    signals = []

    accuracy = inspection.get(
        "gps_accuracy_m"
    )

    if accuracy is None:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="location",
                name="GPS accuracy",
                status="not_available",
                severity="info",
                explanation=(
                    "GPS accuracy was not provided."
                ),
            )
        )

        return signals

    if accuracy <= 10:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="location",
                name="GPS accuracy",
                status="acceptable",
                severity="info",
                score=1.0,
                explanation=(
                    f"Recorded GPS accuracy is "
                    f"{accuracy:.1f} m."
                ),
            )
        )

    else:

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="location",
                name="GPS accuracy",
                status="weak",
                severity="warning",
                score=0.35,
                explanation=(
                    f"Recorded GPS accuracy is "
                    f"{accuracy:.1f} m, reducing confidence "
                    f"in field-location verification."
                ),
            )
        )

    return signals

def _verify_documents(
    inspection_id: str,
    evidence: list[dict],
) -> list[VerificationSignal]:
    """
    Verify uploaded inspection documents.

    This layer does not declare a report fraudulent.

    It produces explainable signals for:
      - PDF extraction
      - numeric extraction
      - exact document duplication
      - semantic similarity with historical documents
    """

    signals: list[VerificationSignal] = []

    document_evidence = [
        item
        for item in evidence
        if str(item.get("evidence_type", "")).lower()
        == "document"
    ]

    if not document_evidence:
        return signals

    current_dir = DOCUMENT_ROOT / inspection_id

    if not current_dir.exists():
        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="document",
                name="Document storage",
                status="storage_missing",
                severity="high",
                score=0.0,
                explanation=(
                    "A document evidence record exists, "
                    "but its local document storage could not "
                    "be found."
                ),
            )
        )
        return signals

    for evidence_item in document_evidence:

        filename = evidence_item.get("filename")

        if not filename:
            continue

        path = current_dir / filename

        # ----------------------------------------------------
        # Storage integrity
        # ----------------------------------------------------

        if not path.exists():

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document availability",
                    status="file_missing",
                    severity="high",
                    score=0.0,
                    explanation=(
                        f"Registered document '{filename}' "
                        "could not be found in the expected "
                        "inspection storage location."
                    ),
                )
            )

            continue

        # ----------------------------------------------------
        # SHA-256 integrity
        # ----------------------------------------------------

        actual_hash = sha256_file(path)

        recorded_hash = evidence_item.get("sha256")

        if recorded_hash and recorded_hash != actual_hash:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document hash integrity",
                    status="hash_mismatch",
                    severity="high",
                    score=0.0,
                    explanation=(
                        f"The SHA-256 hash of '{filename}' "
                        "does not match the hash recorded "
                        "when the evidence was submitted."
                    ),
                )
            )

        else:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document hash integrity",
                    status="passed",
                    severity="info",
                    score=1.0,
                    explanation=(
                        f"SHA-256 integrity check passed "
                        f"for '{filename}'."
                    ),
                )
            )

        # ----------------------------------------------------
        # PDF extraction
        # ----------------------------------------------------

        try:
            text, method = extract_pdf_text(path)

        except Exception as exc:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document text extraction",
                    status="extraction_failed",
                    severity="high",
                    score=0.0,
                    explanation=(
                        f"Document '{filename}' could not "
                        f"be processed: {type(exc).__name__}."
                    ),
                )
            )

            continue

        if not text.strip():

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document text extraction",
                    status="empty_document",
                    severity="warning",
                    score=0.0,
                    explanation=(
                        f"No readable text was extracted "
                        f"from '{filename}'."
                    ),
                )
            )

            continue

        signals.append(
            _signal(
                inspection_id=inspection_id,
                category="document",
                name="Document text extraction",
                status="passed",
                severity="info",
                score=1.0,
                explanation=(
                    f"Readable text was extracted from "
                    f"'{filename}' using {method}."
                ),
            )
        )

        # ----------------------------------------------------
        # Numeric extraction
        # ----------------------------------------------------

        readings = extract_numeric_readings(text)

        extracted_count = sum(
            value is not None
            for value in readings.values()
        )

        if extracted_count:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document measurement extraction",
                    status="passed",
                    severity="info",
                    score=min(
                        extracted_count / 3.0,
                        1.0,
                    ),
                    explanation=(
                        f"Document AI extracted "
                        f"{extracted_count} domain measurement(s) "
                        f"from '{filename}': {readings}."
                    ),
                )
            )

        else:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document",
                    name="Document measurement extraction",
                    status="no_measurements_found",
                    severity="warning",
                    score=0.0,
                    explanation=(
                        f"No supported mine measurement "
                        f"values were extracted from '{filename}'."
                    ),
                )
            )

        # ----------------------------------------------------
        # Exact duplicate detection
        # ----------------------------------------------------

        current_hash = actual_hash

        try:
            historical_documents = (
                db.find_evidence_by_sha256(
                    current_hash,
                    exclude_inspection_id=inspection_id,
                )
            )
        except AttributeError:
            historical_documents = []

        if historical_documents:

            previous_ids = [
                str(item.get("inspection_id"))
                for item in historical_documents
            ]

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document_integrity",
                    name="Exact document duplicate",
                    status="duplicate",
                    severity="high",
                    score=1.0,
                    explanation=(
                        "The uploaded document has the same "
                        "SHA-256 hash as evidence submitted "
                        f"for previous inspection(s): "
                        f"{', '.join(previous_ids)}."
                    ),
                )
            )

        # ----------------------------------------------------
        # Semantic historical similarity
        # ----------------------------------------------------

        try:
            historical_texts = (
                db.get_previous_document_texts(
                    inspection_id
                )
            )
        except AttributeError:
            historical_texts = []

        best_similarity = 0.0
        best_previous_id = None
        best_method = None

        for previous in historical_texts:

            previous_text = (
                previous.get("text", "")
                if isinstance(previous, dict)
                else ""
            )

            if not previous_text.strip():
                continue

            similarity, method = compute_similarity(
                text,
                previous_text,
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_previous_id = (
                    previous.get("inspection_id")
                    if isinstance(previous, dict)
                    else None
                )
                best_method = method

        if best_similarity >= 0.90:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document_integrity",
                    name="Historical document similarity",
                    status="high_similarity",
                    severity="high",
                    score=best_similarity,
                    explanation=(
                        f"Document '{filename}' is highly "
                        f"similar to a previous inspection "
                        f"document"
                        f"{' ' + str(best_previous_id) if best_previous_id else ''}. "
                        f"Semantic similarity: "
                        f"{best_similarity:.2f}. "
                        f"Method: {best_method}."
                    ),
                )
            )

        elif best_similarity >= 0.75:

            signals.append(
                _signal(
                    inspection_id=inspection_id,
                    category="document_integrity",
                    name="Historical document similarity",
                    status="elevated_similarity",
                    severity="warning",
                    score=best_similarity,
                    explanation=(
                        f"Document '{filename}' shows "
                        f"elevated similarity to a previous "
                        f"inspection document"
                        f"{' ' + str(best_previous_id) if best_previous_id else ''}. "
                        f"Similarity: {best_similarity:.2f}. "
                        f"Method: {best_method}."
                    ),
                )
            )

    return signals
# ============================================================
# FINAL EVIDENCE FUSION
# ============================================================

def _fuse(
    inspection_id: str,
    signals: list[VerificationSignal],
    source_anomalies: list[str],
    conflicts: list[str],
) -> VerificationResult:

    # --------------------------------------------------------
    # Count evidence categories
    # --------------------------------------------------------

    high_conflict_signals = [
        signal
        for signal in signals
        if (
            signal.severity == "high"
            and signal.status
            in {
                "conflict",
                "duplicate",
                "failed_items",
                "high_similarity",
            }
        )
    ]

    source_only_signals = [
        signal
        for signal in signals
        if signal.status
        == "source_anomaly"
    ]

    insufficient_signals = [
        signal
        for signal in signals
        if signal.status
        == "insufficient_evidence"
    ]

    critical_threshold_signals = [
        signal
        for signal in signals
        if (
            signal.category == "regulatory_threshold"
            and signal.status in {"threshold_exceeded", "threshold_below_minimum"}
            and signal.severity == "critical"
        )
    ]

    # --------------------------------------------------------
    # RULE 1
    #
    # Multiple independent high-severity conflicts
    # --------------------------------------------------------

    if len(high_conflict_signals) >= 2:

        status = (
            VerificationStatus.REINSPECTION_RECOMMENDED
        )

        human_required = True

        recommendation = (
            "Multiple independent evidence conflicts "
            "were detected. Human review and likely "
            "reinspection are recommended."
        )

        confidence = 0.90

    # --------------------------------------------------------
    # RULE 2
    #
    # One strong report-level conflict
    # --------------------------------------------------------

    elif len(high_conflict_signals) == 1:

        status = (
            VerificationStatus.VERIFICATION_REQUIRED
        )

        human_required = True

        recommendation = (
            "A material evidence conflict was detected. "
            "Send the inspection to a human reviewer; "
            "do not treat the automated signal as a fraud verdict."
        )

        confidence = 0.78

    # --------------------------------------------------------
    # RULE 3
    #
    # ONLY source anomaly.
    #
    # THIS IS THE CORE FAULT-TOLERANT BEHAVIOUR.
    # --------------------------------------------------------

    elif source_only_signals:

        status = (
            VerificationStatus.SOURCE_ANOMALY
        )

        human_required = False

        recommendation = (
            "One or more source readings appear anomalous, "
            "but independent evidence does not support a "
            "report-level inconsistency. Isolate the faulty "
            "source and continue the inspection without "
            "flagging the report."
        )

        confidence = 0.70

    # --------------------------------------------------------
    # RULE 4
    #
    # Insufficient evidence.
    # --------------------------------------------------------

    elif insufficient_signals:

        status = (
            VerificationStatus.VERIFICATION_REQUIRED
        )

        human_required = True

        recommendation = (
            "Verification evidence is incomplete. "
            "Request additional evidence before making "
            "a compliance-integrity determination."
        )

        confidence = 0.45

    # --------------------------------------------------------
    # RULE 4B
    #
    # Critical Statutory Threshold Breach (e.g. Methane).
    # --------------------------------------------------------

    elif critical_threshold_signals:

        status = (
            VerificationStatus.VERIFICATION_REQUIRED
        )

        human_required = True

        recommendation = (
            "A critical statutory measurement threshold was violated. "
            "Verification requires human regulatory review under CMR 2017."
        )

        confidence = 0.85

    # --------------------------------------------------------
    # RULE 5
    #
    # Everything consistent.
    # --------------------------------------------------------

    else:

        status = (
            VerificationStatus.VERIFIED
        )

        human_required = False

        recommendation = (
            "Available evidence is internally consistent. "
            "No report-level integrity conflict was detected."
        )

        confidence = 0.90

    return VerificationResult(
        verification_id=(
            f"VER-"
            f"{uuid4().hex[:12].upper()}"
        ),
        inspection_id=inspection_id,
        status=status,
        confidence=confidence,
        signals=signals,
        source_anomalies=list(
            dict.fromkeys(
                source_anomalies
            )
        ),
        evidence_conflicts=conflicts,
        recommendation=recommendation,
        human_decision_required=human_required,
    )


# ============================================================
# PUBLIC VERIFICATION FUNCTION
# ============================================================

def verify_inspection(
    inspection_id: str,
) -> VerificationResult:

    data = _get_inspection_data(
        inspection_id
    )

    inspection = data["inspection"]

    mine_id = inspection[
        "mine_id"
    ]

    # --------------------------------------------------------
    # Set inspection state to VERIFYING
    # --------------------------------------------------------

    conn = db._connect()

    conn.execute(
        """
        UPDATE inspections
        SET status = ?
        WHERE inspection_id = ?
        """,
        (
            InspectionStatus.VERIFYING.value,
            inspection_id,
        ),
    )

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # Run evidence layers
    # --------------------------------------------------------

    signals = []

    source_anomalies = []

    conflicts = []

    measurement_signals, measurement_anomalies, measurement_conflicts = (
        _verify_measurements(
            inspection_id,
            mine_id,
            data["measurements"],
        )
    )

    signals.extend(
        measurement_signals
    )

    source_anomalies.extend(
        measurement_anomalies
    )

    conflicts.extend(
        measurement_conflicts
    )

    # --------------------------------------------------------
    # STATUTORY THRESHOLDS
    # --------------------------------------------------------

    threshold_signals = _verify_thresholds(
        inspection_id,
        inspection["template_id"],
        data["measurements"],
    )

    signals.extend(
        threshold_signals
    )
        # --------------------------------------------------------
    # DOCUMENT INTELLIGENCE
    # --------------------------------------------------------

    document_signals = _verify_documents(
        inspection_id,
        data["evidence"],
    )

    signals.extend(
        document_signals
    )

    for sig in document_signals:
        if sig.status == "high_similarity":
            conflicts.append(sig.explanation)

    checklist_signals, checklist_conflicts = (
        _verify_checklist(
            inspection_id,
            data["checklist"],
        )
    )

    signals.extend(
        checklist_signals
    )

    conflicts.extend(
        checklist_conflicts
    )

    evidence_signals, evidence_conflicts = (
        _verify_evidence(
            inspection_id,
            data["evidence"],
        )
    )

    signals.extend(
        evidence_signals
    )

    conflicts.extend(
        evidence_conflicts
    )

    signals.extend(
        _verify_gps(
            inspection_id,
            inspection,
        )
    )

    # --------------------------------------------------------
    # Evidence fusion
    # --------------------------------------------------------

    result = _fuse(
        inspection_id,
        signals,
        source_anomalies,
        conflicts,
    )

    # --------------------------------------------------------
    # Persist verification result
    # --------------------------------------------------------

    db.save_verification_result(
        result
    )

    # --------------------------------------------------------
    # Update inspection status
    # --------------------------------------------------------

    if result.human_decision_required:

        new_status = (
            InspectionStatus.REVIEW_REQUIRED
        )

    elif (
        result.status
        == VerificationStatus.REINSPECTION_RECOMMENDED
    ):

        new_status = (
            InspectionStatus.REINSPECTION_RECOMMENDED
        )

    else:

        new_status = (
            InspectionStatus.VERIFIED
        )

    conn = db._connect()

    conn.execute(
        """
        UPDATE inspections
        SET status = ?
        WHERE inspection_id = ?
        """,
        (
            new_status.value,
            inspection_id,
        ),
    )

    conn.commit()
    conn.close()

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    db.log_event(
        entity_type="inspection",
        entity_id=inspection_id,
        action="verification_completed",
        actor_id="PRITHVI-VERIFICATION-ENGINE",
        details=(
            f"status={result.status.value};"
            f"confidence={result.confidence:.2f};"
            f"human_review={result.human_decision_required}"
        ),
    )

    return result