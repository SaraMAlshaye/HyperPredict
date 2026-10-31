import { calculateBmi, roundBmi } from "./bmi";
import type { AssessmentDraft, ModelSchema, PredictionRequest } from "./types";

/** Height/weight limits for the form (not model features; they only produce BMI). */
export const HEIGHT_RANGE = { min: 100, max: 250 };
export const WEIGHT_RANGE = { min: 25, max: 300 };
/** Typical adult resting pulse. Outside this we warn, but still allow (schema allows 30-220). */
export const TYPICAL_PULSE = { min: 40, max: 120 };

export type FieldErrors = Partial<Record<keyof AssessmentDraft | "bmi", string>>;

/** Parses a typed number; empty or non-numeric text gives null. */
export function parseNumber(text: string): number | null {
  const trimmed = text.trim().replace(",", ".");
  if (trimmed === "" || !/^-?\d+(\.\d+)?$/.test(trimmed)) return null;
  return Number(trimmed);
}

function checkRange(
  text: string, label: string, min: number, max: number, unit: string, integer = false,
): string | undefined {
  if (text.trim() === "") return `Please enter your ${label}.`;
  const value = parseNumber(text);
  if (value === null) return `${capitalise(label)} must be a number.`;
  if (integer && !Number.isInteger(value)) return `${capitalise(label)} must be a whole number.`;
  if (value < min || value > max) return `${capitalise(label)} must be between ${min} and ${max} ${unit}.`;
  return undefined;
}

function capitalise(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Step 1: age, sex, race/ethnicity, height, weight (and the BMI they produce). */
export function validatePersonal(draft: AssessmentDraft, schema: ModelSchema): FieldErrors {
  const errors: FieldErrors = {};
  const age = schema.numeric_inputs.Age_Years;
  errors.age = checkRange(draft.age, "age", age.min, age.max, "years", true);
  if (!schema.categorical_options.Sex.includes(draft.sex)) errors.sex = "Please choose an option.";
  if (!schema.categorical_options.Race_Ethnicity.includes(draft.race)) {
    errors.race = "Please choose an option.";
  }
  errors.heightCm = checkRange(draft.heightCm, "height", HEIGHT_RANGE.min, HEIGHT_RANGE.max, "cm");
  errors.weightKg = checkRange(draft.weightKg, "weight", WEIGHT_RANGE.min, WEIGHT_RANGE.max, "kg");
  if (!errors.heightCm && !errors.weightKg) {
    const bmi = calculateBmi(parseNumber(draft.heightCm)!, parseNumber(draft.weightKg)!);
    const spec = schema.numeric_inputs.BMI;
    if (bmi === null || roundBmi(bmi) < spec.min || roundBmi(bmi) > spec.max) {
      errors.bmi = `This height and weight give a BMI outside ${spec.min}–${spec.max}. Please check both values.`;
    }
  }
  return clean(errors);
}

/** Step 2: resting pulse, entered by hand. */
export function validatePulse(draft: AssessmentDraft, schema: ModelSchema): FieldErrors {
  const spec = schema.numeric_inputs.Pulse_BPM;
  return clean({ pulse: checkRange(draft.pulse, "resting pulse", spec.min, spec.max, "BPM", true) });
}

/** A gentle note (never blocking) when a valid pulse is unusual at rest. */
export function pulseNote(text: string): string | undefined {
  const value = parseNumber(text);
  if (value === null) return undefined;
  if (value < TYPICAL_PULSE.min || value > TYPICAL_PULSE.max) {
    return "That is unusual for a resting pulse. Please double-check it after sitting quietly for 5 minutes.";
  }
  return undefined;
}

/** Builds the API request: exactly the five model features, BMI rounded like NHANES. */
export function toPredictionRequest(draft: AssessmentDraft): PredictionRequest {
  const bmi = calculateBmi(parseNumber(draft.heightCm)!, parseNumber(draft.weightKg)!)!;
  return {
    Age_Years: parseNumber(draft.age)!,
    BMI: roundBmi(bmi),
    Pulse_BPM: parseNumber(draft.pulse)!,
    Sex: draft.sex,
    Race_Ethnicity: draft.race,
  };
}

function clean(errors: FieldErrors): FieldErrors {
  return Object.fromEntries(Object.entries(errors).filter(([, v]) => v)) as FieldErrors;
}
