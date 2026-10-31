import type { CSSProperties } from "react";
import { STATUS_STEPS, STATUS_TEXT, bpmForModel, type SensorState } from "../lib/sensor";
import { Icon } from "./Icon";

/**
 * Visual display of the sensor state. It only ever shows what the sensor reported:
 * no reading means "—", and progress is shown as a percentage only if the device sends one.
 */
export function SensorReading({ state }: { state: SensorState }) {
  const bpm = state.status === "received" ? bpmForModel(state) : null;
  // When a real reading exists, the heart beats at that rate; otherwise it only "breathes".
  const beatStyle = bpm ? ({ "--beat": `${(60 / bpm).toFixed(3)}s` } as CSSProperties) : undefined;

  return (
    <div className={`sensor sensor--${state.status}`}>
      <StatusPill state={state} />

      <div className="sensor__orb" style={beatStyle} aria-hidden="true">
        <span className="sensor__ring sensor__ring--1" />
        <span className="sensor__ring sensor__ring--2" />
        <span className="sensor__ring sensor__ring--3" />
        <span className="sensor__core">
          <svg viewBox="0 0 24 24" className="sensor__heart">
            <path d="M12 20.3s-7.6-4.6-9.1-9.7C1.9 7 4.3 4.4 7.2 4.4c2 0 3.6 1.1 4.8 2.9 1.2-1.8 2.8-2.9 4.8-2.9 2.9 0 5.3 2.6 4.3 6.2-1.5 5.1-9.1 9.7-9.1 9.7z" />
          </svg>
          <svg viewBox="0 0 120 24" className="sensor__trace">
            <path d="M0 12h34l6-9 8 18 7-14 4 5h61" />
          </svg>
        </span>
      </div>

      <div className="sensor__bpm" aria-live="polite">
        <span className="sensor__bpm-value">{bpm ?? "—"}</span>
        <span className="sensor__bpm-unit">BPM</span>
        <span className="visually-hidden">
          {bpm ? `Resting pulse ${bpm} beats per minute` : "No reading yet"}
        </span>
      </div>

      <SensorProgress state={state} />
      <StatusTrack state={state} />
    </div>
  );
}

function StatusPill({ state }: { state: SensorState }) {
  const text = STATUS_TEXT[state.status];
  return (
    <div className="sensor__pill" role="status">
      <span className="sensor__pill-dot" />
      {text.title}
    </div>
  );
}

function SensorProgress({ state }: { state: SensorState }) {
  const { status, progress } = state;
  const determinate = status === "received" || (status === "measuring" && progress !== null);
  const value = status === "received" ? 1 : progress ?? 0;
  const caption =
    status === "waiting" ? "Looking for the sensor…"
    : status === "connected" ? "Ready when you are"
    : status === "measuring" ? (progress !== null ? `Measuring… ${Math.round(progress * 100)}%` : "Measuring…")
    : status === "received" ? "Stable reading captured"
    : state.message ?? STATUS_TEXT.error.detail;

  return (
    <div className="sensor__progress">
      <div
        className={`sensor__bar ${determinate ? "" : "sensor__bar--indeterminate"}`}
        role="progressbar" aria-label="Measurement progress"
        aria-valuemin={0} aria-valuemax={100}
        aria-valuenow={determinate ? Math.round(value * 100) : undefined}
        aria-valuetext={caption}
      >
        <span className="sensor__bar-fill" style={determinate ? { width: `${value * 100}%` } : undefined} />
      </div>
      <p className="sensor__caption">{caption}</p>
    </div>
  );
}

function StatusTrack({ state }: { state: SensorState }) {
  const current = state.status === "error" ? -1 : STATUS_STEPS.indexOf(state.status);
  return (
    <ol className="sensor__track" aria-label="Sensor steps">
      {STATUS_STEPS.map((step, i) => {
        const cls = state.status === "error" ? "is-todo"
          : i < current || (i === current && step === "received") ? "is-done"
          : i === current ? "is-current" : "is-todo";
        return (
          <li key={step} className={`sensor__step ${cls}`}>
            <span className="sensor__step-dot">
              {cls === "is-done" ? <Icon name="check" size={12} /> : null}
            </span>
            <span className="sensor__step-label">{STATUS_TEXT[step].title}</span>
          </li>
        );
      })}
    </ol>
  );
}
