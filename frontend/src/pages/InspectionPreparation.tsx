import {
  ArrowLeft,
  ArrowRight,
  CalendarClock,
  ClipboardCheck,
  FileCheck2,
  Info,
  MapPin,
  ShieldAlert,
} from "lucide-react";

import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getMine } from "../api/mines";
import {
  getMineSchedule,
  type MineInspectionSchedule,
} from "../api/schedules";

import {
  getInspectionTemplates,
  type InspectionTemplate,
} from "../api/inspection";

type InspectorMine = {
  mine_id: string;
  name: string;
};

const INSPECTOR_MINE_ID =
  "MINE-BCCL-JHARIA-01";

function formatDate(value: string | null) {
  if (!value) {
    return "NOT SCHEDULED";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "DATE UNAVAILABLE";
  }

  return date
    .toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
    .toUpperCase();
}

function formatFrequency(
  schedule: MineInspectionSchedule
) {
  if (
    schedule.interval_value !== null &&
    schedule.interval_unit
  ) {
    return `${schedule.interval_value} ${schedule.interval_unit}`;
  }

  return (
    schedule.frequency_type ||
    "SCHEDULED"
  );
}

function InspectionPreparation() {
  const navigate = useNavigate();

  const { scheduleInstanceId } =
    useParams();

  const [mine, setMine] =
    useState<InspectorMine | null>(null);

  const [schedule, setSchedule] =
    useState<MineInspectionSchedule | null>(
      null
    );

  const [template, setTemplate] =
    useState<InspectionTemplate | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function load() {
      if (!scheduleInstanceId) {
        setError(
          "Inspection requirement was not specified."
        );
        setLoading(false);
        return;
      }

      try {
        const [
          mineData,
          scheduleData,
          templateData,
        ] = await Promise.all([
          getMine(INSPECTOR_MINE_ID),
          getMineSchedule(
            INSPECTOR_MINE_ID
          ),
          getInspectionTemplates(),
        ]);

        const selectedSchedule =
          scheduleData.schedules.find(
            (item) =>
              item.schedule_instance_id ===
              scheduleInstanceId
          );

        if (!selectedSchedule) {
          throw new Error(
            "Inspection requirement could not be found."
          );
        }

        const selectedTemplate =
          templateData.find(
            (item) =>
              item.template_id ===
              selectedSchedule.template_id
          );

        setMine(
          mineData as InspectorMine
        );

        setSchedule(
          selectedSchedule
        );

        setTemplate(
          selectedTemplate || null
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load inspection preparation."
        );
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [scheduleInstanceId]);

  const dueState = useMemo(() => {
    if (!schedule?.next_due_at) {
      return "NOT SCHEDULED";
    }

    const due = new Date(
      schedule.next_due_at
    );

    const today = new Date();

    if (due < today) {
      return "OVERDUE";
    }

    if (
      due.toDateString() ===
      today.toDateString()
    ) {
      return "DUE TODAY";
    }

    return "UPCOMING";
  }, [schedule]);

  if (loading) {
    return (
      <div className="field-inspector-page">
        <div className="state-card">
          <div className="state-card-inner">
            <div className="loading-indicator" />
            LOADING INSPECTION DOSSIER...
          </div>
        </div>
      </div>
    );
  }

  if (error || !schedule || !mine) {
    return (
      <div className="field-inspector-page">
        <div className="state-card">
          <div className="state-card-inner">
            {error ||
              "Inspection dossier could not be loaded."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="field-inspector-page inspection-preparation-page">

      {/* =================================================
          BACK
      ================================================= */}

      <button
        className="secondary-action plan-back"
        onClick={() =>
          navigate("/inspections/plan")
        }
      >
        <ArrowLeft size={15} />
        BACK TO INSPECTION PLAN
      </button>


      {/* =================================================
          HERO
      ================================================= */}

      <section className="preparation-hero">

        <div>

          <span className="section-number">
            PRE-INSPECTION DOSSIER
          </span>

          <div className="preparation-code">
            {schedule.schedule_instance_id}
          </div>

          <h1>
            {schedule.schedule_name}
          </h1>

          <p>
            Review the regulatory requirement,
            inspection scope and required field
            evidence before starting the inspection.
          </p>

        </div>

        <div className="preparation-status">

          <span className="preparation-status-label">
            CURRENT STATUS
          </span>

          <strong
            className={
              dueState === "OVERDUE"
                ? "status-overdue"
                : dueState === "DUE TODAY"
                  ? "status-due"
                  : "status-upcoming"
            }
          >
            {dueState}
          </strong>

          <small>
            NEXT DUE{" "}
            {formatDate(
              schedule.next_due_at
            )}
          </small>

        </div>

      </section>


      {/* =================================================
          INSPECTION BASIS
      ================================================= */}

      <section className="preparation-section">

        <div className="preparation-section-heading">

          <div>
            <span className="section-number">
              01 / INSPECTION BASIS
            </span>

            <h2>
              Why this inspection is required
            </h2>
          </div>

        </div>


        <div className="preparation-basis-grid">

          <div className="preparation-basis-card">

            <Info size={17} />

            <span>
              REGULATORY OBLIGATION
            </span>

            <strong>
              {schedule.obligation_id}
            </strong>

          </div>


          <div className="preparation-basis-card">

            <CalendarClock size={17} />

            <span>
              TRIGGER
            </span>

            <strong>
              {schedule.trigger_type}
            </strong>

          </div>


          <div className="preparation-basis-card">

            <ClipboardCheck size={17} />

            <span>
              FREQUENCY
            </span>

            <strong>
              {formatFrequency(schedule)}
            </strong>

          </div>


          <div className="preparation-basis-card">

            <MapPin size={17} />

            <span>
              INSPECTION SCOPE
            </span>

            <strong>
              {mine.name}
            </strong>

          </div>

        </div>


        <div className="preparation-explanation">

          <div className="preparation-explanation-icon">
            <FileCheck2 size={18} />
          </div>

          <div>

            <strong>
              PRITHVI SCHEDULE BASIS
            </strong>

            <p>
              This inspection requirement is
              associated with the active regulatory
              schedule registered for this mine.
              The schedule determines the applicable
              inspection template, regulatory
              obligation, trigger and frequency.
            </p>

          </div>

        </div>

      </section>


      {/* =================================================
          TEMPLATE
      ================================================= */}

      <section className="preparation-section">

        <div className="preparation-section-heading">

          <div>
            <span className="section-number">
              02 / INSPECTION SCOPE
            </span>

            <h2>
              What will be inspected
            </h2>
          </div>

        </div>


        <div className="preparation-template">

          <div className="preparation-template-header">

            <div>

              <span>
                INSPECTION TEMPLATE
              </span>

              <h3>
                {template?.name ||
                  schedule.schedule_name}
              </h3>

            </div>

            <div className="template-id">
              {schedule.template_id}
            </div>

          </div>


          {template?.description && (
            <p className="template-description">
              {template.description}
            </p>
          )}

        </div>

      </section>


      {/* =================================================
          REQUIRED MEASUREMENTS
      ================================================= */}

      {template &&
        template.measurements.length > 0 && (
          <section className="preparation-section">

            <div className="preparation-section-heading">

              <div>

                <span className="section-number">
                  03 / FIELD MEASUREMENTS
                </span>

                <h2>
                  Required readings
                </h2>

              </div>

            </div>


            <div className="preparation-requirement-list">

              {template.measurements.map(
                (measurement) => (
                  <div
                    className="preparation-requirement"
                    key={
                      measurement.measurement_id ||
                      measurement.name
                    }
                  >

                    <div>
                      <strong>
                        {measurement.name}
                      </strong>

                      {measurement.description && (
                        <p>
                          {measurement.description}
                        </p>
                      )}
                    </div>

                    <span>
                      {measurement.unit ||
                        "VALUE"}
                    </span>

                    {measurement.required && (
                      <b>
                        REQUIRED
                      </b>
                    )}

                  </div>
                )
              )}

            </div>

          </section>
        )}


      {/* =================================================
          CHECKLIST
      ================================================= */}

      {template &&
        template.checklist.length > 0 && (
          <section className="preparation-section">

            <div className="preparation-section-heading">

              <div>

                <span className="section-number">
                  04 / FIELD CHECKLIST
                </span>

                <h2>
                  Required checks
                </h2>

              </div>

            </div>


            <div className="preparation-checklist">

              {template.checklist.map(
                (item, index) => (
                  <div
                    className="preparation-checklist-item"
                    key={item.item_id}
                  >

                    <span className="checklist-number">
                      {String(index + 1).padStart(
                        2,
                        "0"
                      )}
                    </span>

                    <div>
                      <strong>
                        {item.question}
                      </strong>

                      {item.severity_if_failed && (
                        <small>
                          FAILURE SEVERITY:{" "}
                          {item.severity_if_failed}
                        </small>
                      )}
                    </div>

                    {item.required && (
                      <b>
                        REQUIRED
                      </b>
                    )}

                  </div>
                )
              )}

            </div>

          </section>
        )}


      {/* =================================================
          EVIDENCE
      ================================================= */}

      {template &&
        template.evidence_requirements.length > 0 && (
          <section className="preparation-section">

            <div className="preparation-section-heading">

              <div>

                <span className="section-number">
                  05 / EVIDENCE
                </span>

                <h2>
                  Required field evidence
                </h2>

              </div>

            </div>


            <div className="preparation-evidence-grid">

              {template.evidence_requirements.map(
                (evidence) => (
                  <div
                    className="preparation-evidence-card"
                    key={evidence.evidence_id}
                  >

                    <FileCheck2 size={17} />

                    <strong>
                      {evidence.name}
                    </strong>

                    <span>
                      {evidence.evidence_type}
                    </span>

                    {evidence.minimum_count && (
                      <small>
                        MINIMUM{" "}
                        {evidence.minimum_count}
                      </small>
                    )}

                    {evidence.required && (
                      <b>
                        REQUIRED
                      </b>
                    )}

                  </div>
                )
              )}

            </div>

          </section>
        )}


      {/* =================================================
          VALIDATION
      ================================================= */}

      <section className="preparation-validation">

        <div>

          <ShieldAlert size={19} />

          <div>

            <span>
              REGULATORY VALIDATION
            </span>

            <strong>
              {schedule.validation_status}
            </strong>

          </div>

        </div>

        <p>
          Review the inspection basis and
          requirements before entering the field.
          Inspection execution and submission remain
          subject to the PRITHVI verification workflow.
        </p>

      </section>


      {/* =================================================
          START
      ================================================= */}

      <section className="preparation-start">

        <div>

          <span className="section-number">
            FIELD EXECUTION
          </span>

          <h2>
            Ready to enter the field?
          </h2>

          <p>
            Starting the inspection will create the
            field inspection record. The subsequent
            verification workflow will determine
            whether the inspection can proceed to
            submission.
          </p>

        </div>

        <button
          className="primary-action preparation-start-button"
          onClick={() =>
            navigate(
              `/inspections/start/${schedule.schedule_instance_id}`
            )
          }
        >
          START INSPECTION
          <ArrowRight size={16} />
        </button>

      </section>

    </div>
  );
}

export default InspectionPreparation;