import { Link, useLocation, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { Icon, type IconName } from "../components/Icon";
import { Pulsie } from "../components/Pulsie";
import { ResultBadge, ScoreRing, ThresholdScale } from "../components/Result";
import { StepIndicator } from "../components/StepIndicator";
import { Disclaimer, EmptyState } from "../components/States";
import { useAppState } from "../lib/AppState";
import { formatDateTime, formatPercent } from "../lib/format";
import { findRecord } from "../lib/history";
import type { HistoryRecord } from "../lib/types";

const GENERAL_TIPS: { icon: IconName; title: string; text: string }[] = [
  { icon: "stethoscope", title: "Measure your blood pressure", text: "A cuff reading at a pharmacy, clinic or with a validated home monitor is the only way to know your numbers." },
  { icon: "shaker", title: "Go easy on salt", text: "Choose fresh foods over processed ones and taste before adding salt." },
  { icon: "run", title: "Move most days", text: "Aim for about 150 minutes of moderate activity a week, like brisk walking." },
  { icon: "moon", title: "Rest and recharge", text: "Regular sleep and time to unwind help your heart and blood vessels." },
];

export function Result() {
  const { id = "" } = useParams();
  const location = useLocation();
  const { resetDraft, schemaState } = useAppState();
  const state = location.state as { record?: HistoryRecord; saved?: boolean } | null;
  const record = state?.record?.id === id ? state.record : findRecord(id);

  if (!record) {
    return (
      <div className="page">
        <EmptyState
          title="Result not found"
          message="This result isn't stored in this browser. It may have been deleted, or history was cleared."
          action={<Button to="/check/about-you" icon="clipboard">Start a new check</Button>}
        />
      </div>
    );
  }

  const { result, inputs } = record;
  const positive = result.label === 1;
  const above = result.probability >= result.threshold;
  const metrics = schemaState.status === "ready" ? schemaState.schema.test_metrics : null;

  return (
    <div className="page page--result">
      <StepIndicator current={2} />
      <header className="page__header">
        <div>
          <h1>Your result</h1>
          <p className="muted">{formatDateTime(record.createdAt)} · {result.modelName} (model v{result.schemaVersion})</p>
        </div>
        <div className="page__header-actions">
          <Button to="/history" variant="secondary" icon="history">History</Button>
          <Button to="/check/about-you" icon="refresh" onClick={resetDraft}>New check</Button>
        </div>
      </header>

      {state?.saved === false && (
        <p className="notice"><Icon name="alert" size={16} /> Your browser blocked local storage, so this result was not added to History.</p>
      )}

      <div className="result-grid">
        <section className={`card result-hero ${positive ? "result-hero--positive" : "result-hero--negative"}`}>
          <div className="result-hero__main">
            <p className="eyebrow">Model prediction</p>
            <ResultBadge label={result.label} text={result.labelText} />
            <h2 className="result-hero__title">
              {positive
                ? "Your profile resembles people who had hypertension in the survey."
                : "Your profile resembles people who did not have hypertension in the survey."}
            </h2>
            <p>
              The model gave your answers a score of <strong>{formatPercent(result.probability)}</strong>,
              which is {above ? "at or above" : "below"} its {formatPercent(result.threshold)} decision
              threshold, so its prediction is <strong>{result.labelText}</strong>.
            </p>
            <ThresholdScale probability={result.probability} threshold={result.threshold} />
          </div>
          <div className="result-hero__visual">
            <ScoreRing probability={result.probability} label={result.label} />
          </div>
        </section>

        <aside className="result-side">
          <Pulsie size="md" speech={positive
            ? "Thanks for checking in! A quick blood-pressure reading is a great next step."
            : "Thanks for checking in! Keep up your healthy habits, and still check your blood pressure now and then."} />
        </aside>
      </div>

      <div className="grid-2">
        <Card title="What this means" icon="info">
          <p>
            The model learned from CDC NHANES 2021–2023 survey data. There, “hypertension” meant a
            measured blood pressure of 130/80 mmHg or higher, or taking blood-pressure medicine.
          </p>
          <p>
            The score shows how strongly your age, sex, background, BMI and resting pulse match people
            in that survey who had hypertension. It is not a measurement of your blood pressure, not a
            personal risk percentage, and not a forecast of the future.
          </p>
          {metrics && (
            <p className="muted">
              On {schemaState.status === "ready" ? schemaState.schema.test_rows.toLocaleString() : ""} survey
              participants it had not seen, the model found {formatPercent(metrics.recall)} of people with
              hypertension and was right {formatPercent(metrics.precision)} of the times it predicted hypertension.
              It can be wrong in both directions.
            </p>
          )}
        </Card>

        <Card title="What you entered" icon="clipboard">
          <dl className="inputs">
            <div><dt>Age</dt><dd>{inputs.age} years</dd></div>
            <div><dt>Sex</dt><dd>{inputs.sex}</dd></div>
            <div><dt>Race / ethnicity</dt><dd>{inputs.race}</dd></div>
            <div><dt>Height · Weight</dt><dd>{inputs.heightCm} cm · {inputs.weightKg} kg</dd></div>
            <div><dt>BMI <span className="tag">sent to model</span></dt><dd>{inputs.bmi.toFixed(1)} kg/m²</dd></div>
            <div><dt>Resting pulse <span className="tag">sent to model</span></dt><dd>{inputs.pulse} BPM</dd></div>
          </dl>
          <p className="muted small">Age, sex and race/ethnicity are also sent. Height and weight are only used to calculate BMI in your browser.</p>
        </Card>
      </div>

      <Card title={positive ? "Suggested next steps" : "Keep your heart healthy"} icon="heart" className="tips-card">
        {positive && (
          <p className="tips-card__lead">
            Consider having your blood pressure measured by a pharmacist, nurse or doctor. They can tell
            you whether you actually have hypertension and what, if anything, to do about it.
          </p>
        )}
        <ul className="tips">
          {GENERAL_TIPS.map((t) => (
            <li key={t.title}>
              <span className="tips__icon"><Icon name={t.icon} size={22} /></span>
              <div><h3>{t.title}</h3><p>{t.text}</p></div>
            </li>
          ))}
        </ul>
        <p className="muted small">General healthy-lifestyle information, not personalised medical advice. <Link to="/learn">Learn more about hypertension</Link>.</p>
      </Card>

      <Disclaimer />
    </div>
  );
}
