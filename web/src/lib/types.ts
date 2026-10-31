/** Shapes returned by the FastAPI backend (api/main.py). */

export interface NumericInputSpec {
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  optional: boolean;
  help: string;
}

export interface ModelSchema {
  model_name: string;
  schema_version: number;
  feature_columns: string[];
  numeric_inputs: Record<string, NumericInputSpec>;
  categorical_options: { Sex: string[]; Race_Ethnicity: string[] };
  decision_threshold: number;
  target_labels: Record<string, string>;
  test_metrics: Record<"accuracy" | "precision" | "recall" | "specificity" | "f1" | "roc_auc", number>;
  test_rows: number;
  disclaimer: string;
}

/** Exactly the five model features. Nothing else is ever sent to /api/predict. */
export interface PredictionRequest {
  Age_Years: number;
  BMI: number;
  Pulse_BPM: number;
  Sex: string;
  Race_Ethnicity: string;
}

export interface PredictionResponse {
  label: 0 | 1;
  label_text: string;
  probability: number;
  decision_threshold: number;
  model_name: string;
  schema_version: number;
  inputs: Record<string, string | number | null>;
  disclaimer: string;
}

/** What the user typed. Height and weight are kept locally to show BMI. */
export interface AssessmentDraft {
  age: string;
  sex: string;
  race: string;
  heightCm: string;
  weightKg: string;
  pulse: string;
}

export interface HistoryRecord {
  id: string;
  createdAt: string;
  result: {
    label: 0 | 1;
    labelText: string;
    probability: number;
    threshold: number;
    modelName: string;
    schemaVersion: number;
  };
  inputs: {
    age: number;
    sex: string;
    race: string;
    heightCm: number;
    weightKg: number;
    bmi: number;
    pulse: number;
  };
}
