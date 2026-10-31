import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { Icon } from "../components/Icon";
import { ResultBadge } from "../components/Result";
import { ScoreChart } from "../components/ScoreChart";
import { EmptyState } from "../components/States";
import { formatDateTime, formatPercent } from "../lib/format";
import { clearHistory, deleteRecord, loadHistory } from "../lib/history";

export function History() {
  const [records, setRecords] = useState(loadHistory);
  const [confirmClear, setConfirmClear] = useState(false);

  const remove = (id: string) => {
    deleteRecord(id);
    setRecords(loadHistory());
  };
  const clearAll = () => {
    clearHistory();
    setRecords(loadHistory());
    setConfirmClear(false);
  };

  return (
    <div className="page page--history">
      <header className="page__header">
        <div>
          <h1>History</h1>
          <p className="muted"><Icon name="shield" size={15} /> Demo data, stored only in this browser (localStorage). Clearing your browser data removes it.</p>
        </div>
        {records.length > 0 && (
          <div className="page__header-actions">
            {confirmClear ? (
              <>
                <span className="muted">Delete all {records.length} results?</span>
                <Button variant="ghost" onClick={() => setConfirmClear(false)}>Cancel</Button>
                <Button variant="danger" icon="trash" onClick={clearAll}>Delete all</Button>
              </>
            ) : (
              <Button variant="secondary" icon="trash" onClick={() => setConfirmClear(true)}>Clear history</Button>
            )}
          </div>
        )}
      </header>

      {records.length === 0 ? (
        <EmptyState
          title="No checks yet"
          message="When you complete a check, your results will appear here so you can look back at them."
          action={<Button to="/check/about-you" icon="clipboard">Start your first check</Button>}
        />
      ) : (
        <>
          {records.length > 1 && (
            <section className="card">
              <h2 className="card__title"><span className="card__icon"><Icon name="pulse" size={18} /></span>Your model scores over time</h2>
              <ScoreChart records={records} threshold={records[0].result.threshold} />
            </section>
          )}
          <ul className="history-list">
            {records.map((r) => (
              <li key={r.id} className="history-item card">
                <span className={`history-item__icon ${r.result.label === 1 ? "is-positive" : ""}`}>
                  <Icon name="heart" size={22} />
                </span>
                <div className="history-item__main">
                  <p className="history-item__date">{formatDateTime(r.createdAt)}</p>
                  <p className="muted small">
                    Age {r.inputs.age} · BMI {r.inputs.bmi.toFixed(1)} · Pulse {r.inputs.pulse} BPM
                  </p>
                </div>
                <ResultBadge label={r.result.label} text={r.result.labelText} small />
                <span className="history-item__score">{formatPercent(r.result.probability)}<small>score</small></span>
                <div className="history-item__actions">
                  <Link to={`/result/${r.id}`} className="icon-btn" aria-label={`View result from ${formatDateTime(r.createdAt)}`}>
                    <Icon name="arrowRight" />
                  </Link>
                  <button type="button" className="icon-btn icon-btn--danger" onClick={() => remove(r.id)}
                          aria-label={`Delete result from ${formatDateTime(r.createdAt)}`}>
                    <Icon name="trash" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
