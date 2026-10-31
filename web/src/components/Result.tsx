import { formatPercent } from "../lib/format";

/** Pill showing the model's label exactly as returned by the backend. */
export function ResultBadge({ label, text, small = false }: { label: 0 | 1; text: string; small?: boolean }) {
  return (
    <span className={`badge ${label === 1 ? "badge--positive" : "badge--negative"} ${small ? "badge--sm" : ""}`}>
      <span className="badge__dot" aria-hidden="true" />
      {text}
    </span>
  );
}

/** Ring showing the model score (probability of the hypertension class). */
export function ScoreRing({ probability, label }: { probability: number; label: 0 | 1 }) {
  const r = 52;
  const c = 2 * Math.PI * r;
  const filled = Math.max(0, Math.min(1, probability)) * c;
  return (
    <div className={`ring ${label === 1 ? "ring--positive" : "ring--negative"}`}>
      <svg viewBox="0 0 120 120" role="img" aria-label={`Model score ${formatPercent(probability)}`}>
        <circle className="ring__track" cx="60" cy="60" r={r} />
        <circle className="ring__value" cx="60" cy="60" r={r}
                strokeDasharray={`${filled} ${c}`} transform="rotate(-90 60 60)" />
      </svg>
      <div className="ring__center" aria-hidden="true">
        <span className="ring__number">{formatPercent(probability)}</span>
        <span className="ring__caption">model score</span>
      </div>
    </div>
  );
}

/** Linear scale 0–100% with the model's decision threshold marked. */
export function ThresholdScale({ probability, threshold }: { probability: number; threshold: number }) {
  const pct = Math.max(0, Math.min(1, probability)) * 100;
  const above = probability >= threshold;
  return (
    <div className="scale" aria-hidden="true">
      <div className="scale__track">
        <div className={`scale__fill ${above ? "is-above" : ""}`} style={{ width: `${pct}%` }} />
        <div className="scale__threshold" style={{ left: `${threshold * 100}%` }} />
        <div className="scale__marker" style={{ left: `${pct}%` }} />
      </div>
      <div className="scale__labels">
        <span>0%</span>
        <span style={{ left: `${threshold * 100}%` }} className="scale__threshold-label">
          {formatPercent(threshold)} decision threshold
        </span>
        <span>100%</span>
      </div>
    </div>
  );
}
