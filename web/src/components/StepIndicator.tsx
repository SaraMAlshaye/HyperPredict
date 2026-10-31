import { Icon } from "./Icon";

const STEPS = ["About you", "Resting pulse", "Your result"];

export function StepIndicator({ current }: { current: 0 | 1 | 2 }) {
  return (
    <ol className="steps" aria-label="Progress">
      {STEPS.map((label, i) => {
        const state = i < current ? "done" : i === current ? "current" : "todo";
        return (
          <li key={label} className={`steps__item steps__item--${state}`}
              aria-current={state === "current" ? "step" : undefined}>
            <span className="steps__dot">{state === "done" ? <Icon name="check" size={14} /> : i + 1}</span>
            <span className="steps__label">{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
