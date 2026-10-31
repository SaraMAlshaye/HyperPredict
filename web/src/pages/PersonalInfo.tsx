import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { ChoiceField, NumberField, SelectField } from "../components/Field";
import { Icon } from "../components/Icon";
import { Pulsie } from "../components/Pulsie";
import { StepIndicator } from "../components/StepIndicator";
import { useAppState } from "../lib/AppState";
import { bmiCategory, calculateBmi, roundBmi } from "../lib/bmi";
import type { ModelSchema } from "../lib/types";
import { HEIGHT_RANGE, WEIGHT_RANGE, parseNumber, validatePersonal, type FieldErrors } from "../lib/validation";
import { SchemaGate } from "./SchemaGate";

export function PersonalInfo() {
  return (
    <div className="page page--form">
      <StepIndicator current={0} />
      <SchemaGate>{(schema) => <PersonalForm schema={schema} />}</SchemaGate>
    </div>
  );
}

function PersonalForm({ schema }: { schema: ModelSchema }) {
  const { draft, updateDraft } = useAppState();
  const navigate = useNavigate();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);

  const height = parseNumber(draft.heightCm);
  const weight = parseNumber(draft.weightKg);
  const inRange = height !== null && weight !== null &&
    height >= HEIGHT_RANGE.min && height <= HEIGHT_RANGE.max &&
    weight >= WEIGHT_RANGE.min && weight <= WEIGHT_RANGE.max;
  const bmi = inRange ? calculateBmi(height, weight) : null;
  const ageSpec = schema.numeric_inputs.Age_Years;

  const set = (field: keyof typeof draft) => (value: string) => {
    updateDraft({ [field]: value });
    if (submitted) setErrors(validatePersonal({ ...draft, [field]: value }, schema));
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    const found = validatePersonal(draft, schema);
    setErrors(found);
    if (Object.keys(found).length === 0) navigate("/check/pulse");
  };

  return (
    <div className="form-layout">
      <form className="card form-card" onSubmit={onSubmit} noValidate>
        <header className="form-card__header">
          <h1>Let's check together</h1>
          <p>Tell us a little about yourself. Every field is required.</p>
        </header>

        <div className="form-grid">
          <NumberField
            label="Age" icon="calendar" unit="years" value={draft.age} onChange={set("age")}
            placeholder="e.g. 45" error={errors.age}
            hint={`Adults ${ageSpec.min}–${ageSpec.max}. If you are over ${ageSpec.max}, enter ${ageSpec.max}: the survey records all older ages as ${ageSpec.max}.`}
          />
          <ChoiceField label="Sex" icon="user" value={draft.sex} onChange={set("sex")}
                       options={schema.categorical_options.Sex} error={errors.sex} />
          <div className="form-grid__wide">
            <SelectField
              label="Race / ethnicity" icon="globe" value={draft.race} onChange={set("race")}
              options={schema.categorical_options.Race_Ethnicity} error={errors.race}
              hint="The categories used by the NHANES survey the model learned from."
            />
          </div>
          <NumberField label="Height" icon="ruler" unit="cm" value={draft.heightCm} onChange={set("heightCm")}
                       placeholder="e.g. 165" decimal error={errors.heightCm} />
          <NumberField label="Weight" icon="scale" unit="kg" value={draft.weightKg} onChange={set("weightKg")}
                       placeholder="e.g. 62" decimal error={errors.weightKg} />
        </div>

        <div className={`bmi ${errors.bmi ? "bmi--invalid" : ""}`} aria-live="polite">
          <div className="bmi__value">
            <span className="bmi__label">Your BMI</span>
            <span className="bmi__number">{bmi !== null ? roundBmi(bmi).toFixed(1) : "—"}</span>
            <span className="bmi__unit">kg/m²</span>
          </div>
          <p className="bmi__text">
            {errors.bmi ? <><Icon name="alert" size={15} /> {errors.bmi}</>
              : bmi !== null ? <>{bmiCategory(bmi)} (general adult guide). Only this BMI is sent to the model, not your height or weight.</>
              : "Calculated automatically from your height and weight: weight (kg) ÷ height (m)²."}
          </p>
        </div>

        <div className="form-card__actions">
          <Button to="/" variant="ghost" icon="arrowLeft">Back</Button>
          <Button type="submit" iconRight="arrowRight" size="lg">Next: resting pulse</Button>
        </div>
      </form>

      <aside className="form-aside">
        <Pulsie size="md" speech="Take your time. These five answers are all the model needs." />
        <div className="card card--soft tip">
          <h2 className="card__title"><span className="card__icon"><Icon name="info" size={18} /></span>Why these questions?</h2>
          <p>The model was trained on exactly these inputs from the CDC's NHANES survey. Age and BMI matter most to its estimate.</p>
        </div>
      </aside>
    </div>
  );
}
