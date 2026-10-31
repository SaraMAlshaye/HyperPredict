import { describe, expect, it } from "vitest";
import { bmiCategory, calculateBmi, roundBmi } from "./bmi";
import { HISTORY_KEY, MAX_RECORDS, clearHistory, deleteRecord, findRecord, loadHistory, saveRecord } from "./history";
import type { AssessmentDraft, HistoryRecord, ModelSchema } from "./types";
import { parseNumber, pulseNote, toPredictionRequest, validatePersonal, validatePulse } from "./validation";

// Mirrors the values served by GET /api/schema for model v3.
const schema = {
  model_name: "Logistic Regression",
  schema_version: 3,
  feature_columns: ["Age_Years", "BMI", "Pulse_BPM", "Sex", "Race_Ethnicity"],
  numeric_inputs: {
    Age_Years: { label: "Age", unit: "years", min: 18, max: 80, step: 1, optional: false, help: "" },
    BMI: { label: "BMI", unit: "kg/m²", min: 10, max: 100, step: 0.1, optional: true, help: "" },
    Pulse_BPM: { label: "Resting pulse", unit: "beats/min", min: 30, max: 220, step: 1, optional: true, help: "" },
  },
  categorical_options: {
    Sex: ["Female", "Male"],
    Race_Ethnicity: ["Mexican American", "Non-Hispanic Asian", "Non-Hispanic Black",
      "Non-Hispanic White", "Other Hispanic", "Other/Multi-Racial"],
  },
  decision_threshold: 0.5,
  target_labels: { "0": "No hypertension", "1": "Hypertension" },
  test_metrics: { accuracy: 0.72, precision: 0.73, recall: 0.75, specificity: 0.69, f1: 0.74, roc_auc: 0.79 },
  test_rows: 1217,
  disclaimer: "",
} as ModelSchema;

const valid: AssessmentDraft = {
  age: "45", sex: "Female", race: "Non-Hispanic Asian", heightCm: "165", weightKg: "62", pulse: "72",
};

describe("BMI", () => {
  it("uses weight / height(m)²", () => {
    expect(calculateBmi(165, 62)).toBeCloseTo(62 / (1.65 * 1.65), 10);
    expect(roundBmi(calculateBmi(180, 81)!)).toBe(25);
    expect(roundBmi(22.749)).toBe(22.7);
    // regression: 80 kg at 160 cm is exactly 31.25 and must round to 31.3, not 31.2
    expect(calculateBmi(160, 80)).toBe(31.25);
    expect(roundBmi(calculateBmi(160, 80)!)).toBe(31.3);
  });
  it("rejects impossible values", () => {
    expect(calculateBmi(0, 60)).toBeNull();
    expect(calculateBmi(170, -1)).toBeNull();
    expect(calculateBmi(Number.NaN, 60)).toBeNull();
  });
  it("labels WHO categories", () => {
    expect(bmiCategory(18)).toMatch(/Underweight/);
    expect(bmiCategory(22)).toMatch(/Healthy/);
    expect(bmiCategory(27)).toMatch(/Overweight/);
    expect(bmiCategory(31)).toMatch(/Obesity/);
  });
});

describe("validation", () => {
  it("accepts a complete, valid form", () => {
    expect(validatePersonal(valid, schema)).toEqual({});
    expect(validatePulse(valid, schema)).toEqual({});
  });
  it("parses numbers strictly", () => {
    expect(parseNumber(" 72 ")).toBe(72);
    expect(parseNumber("1,5")).toBe(1.5);
    expect(parseNumber("72bpm")).toBeNull();
    expect(parseNumber("")).toBeNull();
  });
  it("requires every field", () => {
    const empty: AssessmentDraft = { age: "", sex: "", race: "", heightCm: "", weightKg: "", pulse: "" };
    expect(Object.keys(validatePersonal(empty, schema)).sort()).toEqual(["age", "heightCm", "race", "sex", "weightKg"]);
    expect(validatePulse(empty, schema).pulse).toMatch(/enter/);
  });
  it("enforces the model's ranges from the schema", () => {
    expect(validatePersonal({ ...valid, age: "17" }, schema).age).toMatch(/between 18 and 80/);
    expect(validatePersonal({ ...valid, age: "45.5" }, schema).age).toMatch(/whole number/);
    expect(validatePersonal({ ...valid, sex: "Other" }, schema).sex).toBeDefined();
    expect(validatePulse({ ...valid, pulse: "250" }, schema).pulse).toMatch(/between 30 and 220/);
    expect(validatePulse({ ...valid, pulse: "abc" }, schema).pulse).toMatch(/number/);
  });
  it("blocks height/weight combinations whose BMI the model can't accept", () => {
    expect(validatePersonal({ ...valid, heightCm: "250", weightKg: "25" }, schema).bmi).toMatch(/BMI outside/);
  });
  it("only warns (does not block) on an unusual but valid pulse", () => {
    expect(validatePulse({ ...valid, pulse: "35" }, schema)).toEqual({});
    expect(pulseNote("35")).toMatch(/unusual/);
    expect(pulseNote("72")).toBeUndefined();
  });
  it("sends exactly the five model features, never height or weight", () => {
    const req = toPredictionRequest(valid);
    expect(Object.keys(req).sort()).toEqual(["Age_Years", "BMI", "Pulse_BPM", "Race_Ethnicity", "Sex"]);
    expect(req).toEqual({ Age_Years: 45, BMI: 22.8, Pulse_BPM: 72, Sex: "Female", Race_Ethnicity: "Non-Hispanic Asian" });
  });
});

class MemoryStorage {
  data = new Map<string, string>();
  getItem(k: string) { return this.data.get(k) ?? null; }
  setItem(k: string, v: string) { this.data.set(k, v); }
  removeItem(k: string) { this.data.delete(k); }
}

function record(id: string, probability = 0.6): HistoryRecord {
  return {
    id, createdAt: new Date(2026, 9, 31).toISOString(),
    result: { label: probability >= 0.5 ? 1 : 0, labelText: probability >= 0.5 ? "Hypertension" : "No hypertension",
      probability, threshold: 0.5, modelName: "Logistic Regression", schemaVersion: 3 },
    inputs: { age: 45, sex: "Female", race: "Non-Hispanic Asian", heightCm: 165, weightKg: 62, bmi: 22.8, pulse: 72 },
  };
}

describe("history (localStorage)", () => {
  it("is empty at first", () => {
    expect(loadHistory(new MemoryStorage())).toEqual([]);
  });
  it("saves newest first, finds and deletes records", () => {
    const s = new MemoryStorage();
    expect(saveRecord(record("a", 0.3), s)).toBe(true);
    saveRecord(record("b", 0.7), s);
    expect(loadHistory(s).map((r) => r.id)).toEqual(["b", "a"]);
    expect(findRecord("a", s)?.result.probability).toBe(0.3);
    deleteRecord("b", s);
    expect(loadHistory(s).map((r) => r.id)).toEqual(["a"]);
    clearHistory(s);
    expect(loadHistory(s)).toEqual([]);
  });
  it("keeps at most MAX_RECORDS", () => {
    const s = new MemoryStorage();
    for (let i = 0; i < MAX_RECORDS + 5; i++) saveRecord(record(String(i)), s);
    expect(loadHistory(s)).toHaveLength(MAX_RECORDS);
  });
  it("ignores corrupt or foreign data instead of crashing", () => {
    const s = new MemoryStorage();
    s.setItem(HISTORY_KEY, "{not json");
    expect(loadHistory(s)).toEqual([]);
    s.setItem(HISTORY_KEY, JSON.stringify([{ id: 1 }, record("ok")]));
    expect(loadHistory(s).map((r) => r.id)).toEqual(["ok"]);
  });
  it("reports failure when storage is unavailable or full", () => {
    expect(saveRecord(record("x"), null)).toBe(false);
    const full = new MemoryStorage();
    full.setItem = () => { throw new Error("QuotaExceededError"); };
    expect(saveRecord(record("x"), full)).toBe(false);
  });
});
