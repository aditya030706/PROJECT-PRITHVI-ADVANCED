import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  LoaderCircle,
  MapPin,
  ShieldCheck,
} from "lucide-react";

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

import { createInspection } from "../api/inspections";

import {
  getMineSchedule,
  type MineInspectionSchedule,
} from "../api/schedules";

import { getMine } from "../api/mines";


const INSPECTOR_MINE_ID =
  "MINE-BCCL-JHARIA-01";


function StartInspection() {

  const navigate = useNavigate();

  const { scheduleInstanceId } =
    useParams();

  const { session } = useAuth();


  const [schedule, setSchedule] =
    useState<MineInspectionSchedule | null>(
      null
    );

  const [mineName, setMineName] =
    useState("");


  const [latitude, setLatitude] =
    useState<number | null>(null);

  const [longitude, setLongitude] =
    useState<number | null>(null);

  const [accuracy, setAccuracy] =
    useState<number | null>(null);


  const [loading, setLoading] =
    useState(true);

  const [starting, setStarting] =
    useState(false);

  const [gpsLoading, setGpsLoading] =
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
          scheduleData,
          mineData,
        ] = await Promise.all([

          getMineSchedule(
            INSPECTOR_MINE_ID
          ),

          getMine(
            INSPECTOR_MINE_ID
          ),

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


        setSchedule(
          selectedSchedule
        );

        setMineName(
          (mineData as { name: string }).name
        );

      } catch (err) {

        setError(
          err instanceof Error
            ? err.message
            : "Unable to prepare inspection."
        );

      } finally {

        setLoading(false);

      }

    }


    load();

  }, [scheduleInstanceId]);


  useEffect(() => {

    if (!navigator.geolocation) {

      setGpsLoading(false);

      setError(
        "This device does not provide GPS location."
      );

      return;
    }


    navigator.geolocation.getCurrentPosition(

      (position) => {

        setLatitude(
          position.coords.latitude
        );

        setLongitude(
          position.coords.longitude
        );

        setAccuracy(
          position.coords.accuracy
        );

        setGpsLoading(false);

      },

      () => {

        setGpsLoading(false);

        setError(
          "GPS location is required to start this field inspection."
        );

      },

      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0,
      }

    );

  }, []);


  async function handleStart() {

    if (!schedule) {
      return;
    }


    if (
      latitude === null ||
      longitude === null
    ) {

      setError(
        "GPS position is required before starting the inspection."
      );

      return;
    }


    setStarting(true);

    setError(null);


    try {

      const inspection =
        await createInspection({

          mine_id:
            INSPECTOR_MINE_ID,

          template_id:
            schedule.template_id,

          obligation_id:
            schedule.obligation_id,

          inspector_id:
            session?.user_id || "INSPECTOR-01",

          inspection_date:
            new Date()
              .toISOString()
              .slice(0, 10),

          latitude,

          longitude,

          gps_accuracy_m:
            accuracy ?? undefined,

        });


      navigate(
        `/inspections/${inspection.inspection_id}`
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start inspection."
      );

    } finally {

      setStarting(false);

    }

  }


  if (loading) {

    return (
      <div className="inspection-start-page">

        <div className="state-card">

          <div className="state-card-inner">

            <LoaderCircle
              size={18}
              className="spin"
            />

            LOADING INSPECTION REQUIREMENT...

          </div>

        </div>

      </div>
    );

  }


  if (!schedule) {

    return (
      <div className="inspection-start-page">

        <div className="state-card state-error">

          <div className="state-card-inner">

            {error ||
              "Inspection requirement unavailable."}

          </div>

        </div>

      </div>
    );

  }


  return (

    <div className="inspection-start-page">

      <button
        className="secondary-action"
        onClick={() =>
          navigate(-1)
        }
      >

        <ArrowLeft size={15} />

        BACK

      </button>


      <section className="start-hero">

        <span className="section-number">
          FIELD EXECUTION / START GATE
        </span>

        <h1>
          Start field inspection
        </h1>

        <p>
          PRITHVI will create the inspection record
          using the selected regulatory requirement,
          assigned mine, inspector identity and
          captured field location.
        </p>

      </section>


      {error && (

        <div className="inline-error">

          <MapPin size={14} />

          {error}

        </div>

      )}


      <section className="start-verification-grid">

        <div className="start-verification-card">

          <CheckCircle2 size={18} />

          <span>
            INSPECTOR
          </span>

          <strong>
            {session?.name || "Inspector"}
          </strong>

          <small>
            {session?.user_id || "INSPECTOR-01"}
          </small>

        </div>


        <div className="start-verification-card">

          <CheckCircle2 size={18} />

          <span>
            ASSIGNED MINE
          </span>

          <strong>
            {mineName}
          </strong>

          <small>
            {INSPECTOR_MINE_ID}
          </small>

        </div>


        <div className="start-verification-card">

          <CheckCircle2 size={18} />

          <span>
            REGULATORY BASIS
          </span>

          <strong>
            {schedule.obligation_id}
          </strong>

          <small>
            {schedule.schedule_name}
          </small>

        </div>


        <div
          className={
            latitude !== null
              ? "start-verification-card gps-ready"
              : "start-verification-card"
          }
        >

          <MapPin size={18} />

          <span>
            FIELD LOCATION
          </span>

          <strong>
            {gpsLoading
              ? "CAPTURING GPS..."
              : latitude !== null
                ? "GPS CAPTURED"
                : "GPS UNAVAILABLE"}
          </strong>

          <small>
            {latitude !== null
              ? `${latitude.toFixed(6)}, ${longitude?.toFixed(6)}`
              : "Location required"}
          </small>

        </div>

      </section>


      <section className="start-security-panel">

        <div>

          <ShieldCheck size={20} />

          <div>

            <span>
              PRITHVI FIELD CONTROL
            </span>

            <strong>
              Inspection identity and location captured
              at session start.
            </strong>

          </div>

        </div>

        <p>
          The inspection will be created against the
          selected regulatory schedule. The captured
          GPS position and timestamp become part of the
          inspection record.
        </p>

      </section>


      <footer className="start-action-bar">

        <div>

          <span>
            READY TO START
          </span>

          <strong>
            {schedule.schedule_name}
          </strong>

        </div>


        <button
          className="primary-action"
          onClick={handleStart}
          disabled={
            starting ||
            gpsLoading ||
            latitude === null
          }
        >

          {starting
            ? "CREATING INSPECTION..."
            : "START INSPECTION"}

          {starting ? (
            <LoaderCircle
              size={15}
              className="spin"
            />
          ) : (
            <ArrowRight size={15} />
          )}

        </button>

      </footer>

    </div>

  );

}


export default StartInspection;