import { useId } from "react";
import { Icon, type IconName } from "./Icon";

interface BaseProps {
  label: string;
  icon?: IconName;
  error?: string;
  hint?: string;
}

function Messages({ id, error, hint }: { id: string; error?: string; hint?: string }) {
  return (
    <>
      {hint && !error && <p id={`${id}-hint`} className="field__hint">{hint}</p>}
      {error && (
        <p id={`${id}-error`} className="field__error" role="alert">
          <Icon name="alert" size={15} /> {error}
        </p>
      )}
    </>
  );
}

export function NumberField({ label, icon, error, hint, value, onChange, unit, placeholder, decimal = false }: BaseProps & {
  value: string; onChange: (v: string) => void; unit: string; placeholder?: string; decimal?: boolean;
}) {
  const id = useId();
  return (
    <div className={`field ${error ? "field--invalid" : ""}`}>
      <label htmlFor={id} className="field__label">
        {icon && <span className="field__icon"><Icon name={icon} size={18} /></span>}
        {label}
      </label>
      <div className="field__control">
        <input
          id={id} type="text" inputMode={decimal ? "decimal" : "numeric"} autoComplete="off"
          value={value} placeholder={placeholder} onChange={(e) => onChange(e.target.value)}
          aria-invalid={!!error} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        />
        <span className="field__unit" aria-hidden="true">{unit}</span>
      </div>
      <Messages id={id} error={error} hint={hint} />
    </div>
  );
}

export function SelectField({ label, icon, error, hint, value, onChange, options, placeholder = "Choose…" }: BaseProps & {
  value: string; onChange: (v: string) => void; options: string[]; placeholder?: string;
}) {
  const id = useId();
  return (
    <div className={`field ${error ? "field--invalid" : ""}`}>
      <label htmlFor={id} className="field__label">
        {icon && <span className="field__icon"><Icon name={icon} size={18} /></span>}
        {label}
      </label>
      <div className="field__control field__control--select">
        <select
          id={id} value={value} onChange={(e) => onChange(e.target.value)}
          aria-invalid={!!error} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        >
          <option value="" disabled>{placeholder}</option>
          {options.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
      </div>
      <Messages id={id} error={error} hint={hint} />
    </div>
  );
}

/** Two or three options as large toggle buttons (used for Sex). */
export function ChoiceField({ label, icon, error, value, onChange, options }: BaseProps & {
  value: string; onChange: (v: string) => void; options: string[];
}) {
  const id = useId();
  return (
    <fieldset className={`field ${error ? "field--invalid" : ""}`} aria-describedby={error ? `${id}-error` : undefined}>
      <legend className="field__label">
        {icon && <span className="field__icon"><Icon name={icon} size={18} /></span>}
        {label}
      </legend>
      <div className="choice" role="radiogroup">
        {options.map((o) => (
          <button
            key={o} type="button" role="radio" aria-checked={value === o}
            className={`choice__option ${value === o ? "is-selected" : ""}`} onClick={() => onChange(o)}
          >
            {value === o && <Icon name="check" size={16} />} {o}
          </button>
        ))}
      </div>
      <Messages id={id} error={error} />
    </fieldset>
  );
}
