import { describe, expect, it } from "vitest";
import {
  INITIAL_SENSOR_STATE, NoSensorSource, STATUS_STEPS, STATUS_TEXT, bpmForModel, createSensorSource,
  isUsableReading, type SensorState,
} from "./sensor";
import { toPredictionRequest } from "./validation";

const RANGE = { min: 30, max: 220 }; // Pulse_BPM range from the model schema

function state(patch: Partial<SensorState>): SensorState {
  return { ...INITIAL_SENSOR_STATE, ...patch };
}

describe("sensor source (no hardware yet)", () => {
  it("defaults to the no-sensor source", () => {
    expect(createSensorSource().kind).toBe("none");
  });

  it("reports waiting and never produces a reading", () => {
    const seen: SensorState[] = [];
    const source = new NoSensorSource();
    const unsubscribe = source.subscribe((s) => seen.push(s));
    source.start();
    source.start();
    source.stop();
    unsubscribe();
    expect(seen.length).toBeGreaterThan(0);
    for (const s of seen) {
      expect(s.status).toBe("waiting");
      expect(s.bpm).toBeNull();
      expect(s.progress).toBeNull();
    }
  });

  it("starts with no BPM, no progress and no timestamp", () => {
    expect(INITIAL_SENSOR_STATE).toEqual({
      status: "waiting", bpm: null, progress: null, message: null, receivedAt: null,
    });
  });
});

describe("when Continue is allowed", () => {
  it("is blocked for every status except a received reading", () => {
    for (const status of ["waiting", "connected", "measuring", "error"] as const) {
      expect(isUsableReading(state({ status, bpm: 72 }), RANGE)).toBe(false);
    }
  });

  it("is blocked when a received state has no BPM", () => {
    expect(isUsableReading(state({ status: "received", bpm: null }), RANGE)).toBe(false);
  });

  it("accepts a valid reading inside the model's range", () => {
    expect(isUsableReading(state({ status: "received", bpm: 72 }), RANGE)).toBe(true);
    expect(isUsableReading(state({ status: "received", bpm: 30 }), RANGE)).toBe(true);
    expect(isUsableReading(state({ status: "received", bpm: 220 }), RANGE)).toBe(true);
  });

  it("rejects implausible or broken values", () => {
    for (const bpm of [0, 12, 29.4, 221, 400, Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(isUsableReading(state({ status: "received", bpm }), RANGE)).toBe(false);
    }
  });
});

describe("reading passed to the model", () => {
  it("is rounded to a whole BPM, like the training data", () => {
    expect(bpmForModel(state({ status: "received", bpm: 71.6 }))).toBe(72);
    expect(bpmForModel(INITIAL_SENSOR_STATE)).toBeNull();
  });

  it("only fills Pulse_BPM; the request still has exactly the five model features", () => {
    const bpm = bpmForModel(state({ status: "received", bpm: 68.2 }))!;
    const request = toPredictionRequest({
      age: "45", sex: "Female", race: "Non-Hispanic Asian", heightCm: "165", weightKg: "62",
      pulse: String(bpm),
    });
    expect(Object.keys(request).sort()).toEqual(["Age_Years", "BMI", "Pulse_BPM", "Race_Ethnicity", "Sex"]);
    expect(request.Pulse_BPM).toBe(68);
  });
});

describe("status text", () => {
  it("has the five required states", () => {
    expect(Object.values(STATUS_TEXT).map((t) => t.title)).toEqual([
      "Waiting for sensor", "Connected", "Measuring", "Reading received", "Connection error",
    ]);
    expect(STATUS_STEPS).toEqual(["waiting", "connected", "measuring", "received"]);
  });
});
