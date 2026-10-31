import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Icon, type IconName } from "../components/Icon";
import { Pulsie } from "../components/Pulsie";
import { SensorReading } from "../components/SensorReading";
import { StepIndicator } from "../components/StepIndicator";
import { ErrorState } from "../components/States";
import { ApiError, requestPrediction } from "../lib/api";
import { useAppState } from "../lib/AppState";
import { newRecordId, saveRecord } from "../lib/history";
import { STATUS_TEXT, bpmForModel, isUsableReading } from "../lib/sensor";
import type { HistoryRecord, ModelSchema } from "../lib/types";
import { useSensor } from "../lib/useSensor";
import { parseNumber, toPredictionRequest, validatePersonal, validatePulse } from "../lib/validation";
import { SchemaGate } from "./SchemaGate";

const INSTRUCTIONS: { icon: IconName; title: string; text: string }[] = [
  { icon: "hand", title: "Place your finger gently", text: "Rest your fingertip on the MAX30102 sensor without pressing hard." },
  { icon: "shield", title: "Keep your hand still", text: "Movement and talking can disturb the reading." },
  { icon: "timer", title: "Wait for a stable reading", text: "It usually takes a few seconds. The result appears automatically." },
];

export function PulseInfo() {
  return (
    <div className="page page--form">
      <StepIndicator current={1} />
      <SchemaGate>{(schema) => <PulseStep schema={schema} />}</SchemaGate>
    </div>
  );
}

function PulseStep({ schema }: { schema: ModelSchema }) {
  const { draft, updateDraft } = useAppState();
  const navigate = useNavigate();
  const { state, retry } = useSensor();
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);

  // Step 1 must be complete; otherwise send the user back to it.
  if (Object.keys(validatePersonal(draft, schema)).length > 0) {
    return <Navigate to="/check/about-you" replace />;
  }

  const range = schema.numeric_inputs.Pulse_BPM;
  const usable = isUsableReading(state, range);
  const outOfRange = state.status === "received" && !usable;

  const onContinue = async () => {
    const bpm = bpmForModel(state);
    if (!usable || bpm === null) return;
    // The sensor reading fills the same Pulse_BPM field the model has always used.
    const withPulse = { ...draft, pulse: String(bpm) };
    if (Object.keys(validatePulse(withPulse, schema)).length > 0) return;
    updateDraft({ pulse: withPulse.pulse });

    setSubmitting(true);
    setApiError(null);
    try {
      const request = toPredictionRequest(withPulse);
      const response = await requestPrediction(request);
      const record: HistoryRecord = {
        id: newRecordId(),
        createdAt: new Date().toISOString(),
        result: {
          label: response.label,
          labelText: response.label_text,
          probability: response.probability,
          threshold: response.decision_threshold,
          modelName: response.model_name,
          schemaVersion: response.schema_version,
        },
        inputs: {
          age: request.Age_Years, sex: request.Sex, race: request.Race_Ethnicity,
          heightCm: parseNumber(draft.heightCm)!, weightKg: parseNumber(draft.weightKg)!,
          bmi: request.BMI, pulse: request.Pulse_BPM,
        },
      };
      const saved = saveRecord(record);
      navigate(`/result/${record.id}`, { state: { record, saved } });
    } catch (err) {
      setApiError(err instanceof ApiError ? err : new ApiError("Something went wrong while getting your result."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pulse-layout">
      <section className="card pulse-card" aria-labelledby="pulse-title">
        <header className="pulse-card__header">
          <div>
            <p className="eyebrow"><Icon name="pulse" size={16} /> Resting pulse</p>
            <h1 id="pulse-title">Let's measure your heart rate</h1>
            <p className="muted">{STATUS_TEXT[state.status].detail}</p>
          </div>
        </header>

        <SensorReading state={state} />

        {state.status === "error" && (
          <div className="pulse-card__retry">
            <Button variant="secondary" icon="refresh" onClick={retry}>Try connecting again</Button>
          </div>
        )}
        {outOfRange && (
          <p className="notice" role="alert">
            <Icon name="alert" size={16} /> The sensor reported a value outside {range.min}–{range.max} BPM.
            Please keep still and measure again.
          </p>
        )}
        {apiError && (
          <ErrorState title="We couldn't get your result" message={apiError.message} details={apiError.details} />
        )}

        <div className="form-card__actions">
          <Button to="/check/about-you" variant="ghost" icon="arrowLeft">Back</Button>
          <div className="pulse-card__continue">
            <Button iconRight="arrowRight" size="lg" onClick={onContinue}
                    disabled={!usable} loading={submitting}>
              {submitting ? "Asking the model…" : "Continue"}
            </Button>
            {!usable && !submitting && (
              <span className="pulse-card__hint">Available after a valid reading</span>
            )}
          </div>
        </div>
      </section>

      <aside className="pulse-aside">
        <Pulsie size="sm" speech="Relax for a moment. I'll keep an eye on the sensor!" />

        <div className="card instructions">
          <h2 className="card__title"><span className="card__icon"><Icon name="info" size={18} /></span>How to measure</h2>
          <ol className="instructions__list">
            {INSTRUCTIONS.map((step, i) => (
              <li key={step.title}>
                <span className="instructions__icon"><Icon name={step.icon} size={20} /></span>
                <div>
                  <h3><span className="instructions__num">{i + 1}.</span> {step.title}</h3>
                  <p>{step.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <div className="rest-note">
          <Icon name="moon" size={18} />
          <p>
            <strong>Measure while resting.</strong> Sit quietly for about 5 minutes first. The model
            learned from pulses measured at rest, so a calm reading matches best.
          </p>
        </div>
      </aside>
    </div>
  );
}
