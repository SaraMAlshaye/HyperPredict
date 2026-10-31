import type { HistoryRecord } from "../lib/types";
import { formatDate, formatPercent } from "../lib/format";

/** Model scores of past checks over time (oldest left), with the decision threshold. */
export function ScoreChart({ records, threshold }: { records: HistoryRecord[]; threshold: number }) {
  const points = [...records].reverse(); // oldest first
  // Left margin is wider than the right so the "100%" axis label is not clipped.
  const W = 640, H = 180, PL = 48, PR = 24, PY = 20;
  const x = (i: number) => (points.length === 1 ? (PL + W - PR) / 2 : PL + (i * (W - PL - PR)) / (points.length - 1));
  const y = (p: number) => H - PY - p * (H - 2 * PY);
  const line = points.map((r, i) => `${x(i)},${y(r.result.probability)}`).join(" ");
  const area = `${x(0)},${H - PY} ${line} ${x(points.length - 1)},${H - PY}`;

  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
           aria-label={`Model scores of your last ${points.length} checks, oldest to newest`}>
        <defs>
          <linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map((t) => (
          <g key={t}>
            <line x1={PL} x2={W - PR} y1={y(t)} y2={y(t)}
                  className={t === threshold ? "chart__threshold" : "chart__grid"} />
            <text x={PL - 8} y={y(t) + 4} className="chart__axis" textAnchor="end">{formatPercent(t)}</text>
          </g>
        ))}
        {points.length > 1 && <polygon points={area} fill="url(#chartFill)" />}
        {points.length > 1 && <polyline points={line} className="chart__line" />}
        {points.map((r, i) => (
          <circle key={r.id} cx={x(i)} cy={y(r.result.probability)} r={5}
                  className={r.result.label === 1 ? "chart__dot chart__dot--positive" : "chart__dot"}>
            <title>{`${formatDate(r.createdAt)}: ${formatPercent(r.result.probability)} (${r.result.labelText})`}</title>
          </circle>
        ))}
      </svg>
      <figcaption>Model score per check, oldest to newest. Dashed line: {formatPercent(threshold)} decision threshold.</figcaption>
    </figure>
  );
}
