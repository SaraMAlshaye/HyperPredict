import type { HistoryRecord } from "./types";

/**
 * Prediction history kept in the browser's localStorage. Demo storage only:
 * it stays on this device, is not backed up, and is cleared with browser data.
 */
export const HISTORY_KEY = "hyperpredict.history.v1";
export const MAX_RECORDS = 50;

type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">;

function defaultStorage(): StorageLike | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null; // storage blocked (private mode, browser settings)
  }
}

function isRecord(value: unknown): value is HistoryRecord {
  const r = value as HistoryRecord;
  return (
    !!r && typeof r.id === "string" && typeof r.createdAt === "string" &&
    !!r.result && (r.result.label === 0 || r.result.label === 1) &&
    typeof r.result.probability === "number" && !!r.inputs
  );
}

/** Newest first. Corrupt or foreign data is ignored rather than crashing the page. */
export function loadHistory(storage: StorageLike | null = defaultStorage()): HistoryRecord[] {
  if (!storage) return [];
  try {
    const raw = storage.getItem(HISTORY_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter(isRecord) : [];
  } catch {
    return [];
  }
}

/** Returns false if the browser refused to store it (the result is still shown). */
export function saveRecord(record: HistoryRecord, storage: StorageLike | null = defaultStorage()): boolean {
  if (!storage) return false;
  try {
    const next = [record, ...loadHistory(storage).filter((r) => r.id !== record.id)].slice(0, MAX_RECORDS);
    storage.setItem(HISTORY_KEY, JSON.stringify(next));
    return true;
  } catch {
    return false;
  }
}

export function findRecord(id: string, storage: StorageLike | null = defaultStorage()): HistoryRecord | undefined {
  return loadHistory(storage).find((r) => r.id === id);
}

export function deleteRecord(id: string, storage: StorageLike | null = defaultStorage()): void {
  if (!storage) return;
  try {
    storage.setItem(HISTORY_KEY, JSON.stringify(loadHistory(storage).filter((r) => r.id !== id)));
  } catch {
    /* ignore: nothing else to do if storage is unavailable */
  }
}

export function clearHistory(storage: StorageLike | null = defaultStorage()): void {
  try {
    storage?.removeItem(HISTORY_KEY);
  } catch {
    /* ignore */
  }
}

export function newRecordId(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
