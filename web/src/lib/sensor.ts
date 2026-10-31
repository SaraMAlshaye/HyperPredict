/**
 * Sensor state for the Resting Pulse page, kept separate from the UI so the
 * Arduino/ESP32 + MAX30102 connection can be added later without touching the page.
 *
 * Today the app uses NoSensorSource: it reports "waiting" forever and NEVER produces
 * a reading. No BPM value is invented anywhere in this file.
 *
 * To connect hardware later, implement SensorSource (for example with the browser's
 * Web Serial API, or by streaming from the Python layer in iot/sensor_source.py) and
 * return it from createSensorSource(). The page needs no other change.
 */

export type SensorStatus = "waiting" | "connected" | "measuring" | "received" | "error";

export interface SensorState {
  status: SensorStatus;
  /** Heart rate in BPM. Only set by a real device, with status "received". */
  bpm: number | null;
  /** 0–1 while measuring, only if the device reports progress; otherwise null. */
  progress: number | null;
  /** Detail text, e.g. the reason for a connection error. */
  message: string | null;
  /** When the reading arrived (ISO time), set together with bpm. */
  receivedAt: string | null;
}

export const INITIAL_SENSOR_STATE: SensorState = {
  status: "waiting", bpm: null, progress: null, message: null, receivedAt: null,
};

export interface SensorSource {
  /** Short name shown in debugging, e.g. "none" or "web-serial". */
  readonly kind: string;
  /** Calls `listener` with the current state now and on every change. Returns unsubscribe. */
  subscribe(listener: (state: SensorState) => void): () => void;
  /** Ask the device to (re)start a measurement. */
  start(): void;
  /** Stop listening and release the device. */
  stop(): void;
}

/** The only source for now: no hardware connected, so it waits and never reads. */
export class NoSensorSource implements SensorSource {
  readonly kind = "none";
  subscribe(listener: (state: SensorState) => void): () => void {
    listener(INITIAL_SENSOR_STATE);
    return () => {};
  }
  start(): void {}
  stop(): void {}
}

/** Single place to choose the sensor implementation. */
export function createSensorSource(): SensorSource {
  return new NoSensorSource();
}

export interface BpmRange {
  min: number;
  max: number;
}

/** A reading can be used only if a device reported it and it is inside the model's range. */
export function isUsableReading(state: SensorState, range: BpmRange): boolean {
  return (
    state.status === "received" &&
    typeof state.bpm === "number" &&
    Number.isFinite(state.bpm) &&
    Math.round(state.bpm) >= range.min &&
    Math.round(state.bpm) <= range.max
  );
}

/** The model's Pulse_BPM is a whole number of beats per minute. */
export function bpmForModel(state: SensorState): number | null {
  return state.bpm === null ? null : Math.round(state.bpm);
}

export const STATUS_TEXT: Record<SensorStatus, { title: string; detail: string }> = {
  waiting: {
    title: "Waiting for sensor",
    detail: "Connect the HyperPredict pulse sensor to begin.",
  },
  connected: {
    title: "Connected",
    detail: "Sensor ready. Place your finger gently on it.",
  },
  measuring: {
    title: "Measuring",
    detail: "Hold still while the sensor reads your pulse.",
  },
  received: {
    title: "Reading received",
    detail: "Your resting pulse has been recorded.",
  },
  error: {
    title: "Connection error",
    detail: "We couldn't read from the sensor. Check the cable and try again.",
  },
};

/** Order of the normal journey, used for the progress track (error is shown separately). */
export const STATUS_STEPS: SensorStatus[] = ["waiting", "connected", "measuring", "received"];
