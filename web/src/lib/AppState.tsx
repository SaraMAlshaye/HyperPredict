import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { ApiError, fetchSchema } from "./api";
import type { AssessmentDraft, ModelSchema } from "./types";

const DRAFT_KEY = "hyperpredict.draft.v1";
export const EMPTY_DRAFT: AssessmentDraft = {
  age: "", sex: "", race: "", heightCm: "", weightKg: "", pulse: "",
};

type SchemaState =
  | { status: "loading" }
  | { status: "ready"; schema: ModelSchema }
  | { status: "error"; error: ApiError };

interface AppState {
  schemaState: SchemaState;
  reloadSchema: () => void;
  draft: AssessmentDraft;
  updateDraft: (patch: Partial<AssessmentDraft>) => void;
  resetDraft: () => void;
}

const Ctx = createContext<AppState | null>(null);

function readDraft(): AssessmentDraft {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY);
    return raw ? { ...EMPTY_DRAFT, ...JSON.parse(raw) } : EMPTY_DRAFT;
  } catch {
    return EMPTY_DRAFT;
  }
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [schemaState, setSchemaState] = useState<SchemaState>({ status: "loading" });
  const [draft, setDraft] = useState<AssessmentDraft>(readDraft);

  const reloadSchema = useCallback(() => {
    setSchemaState({ status: "loading" });
    fetchSchema()
      .then((schema) => setSchemaState({ status: "ready", schema }))
      .catch((err: unknown) => setSchemaState({
        status: "error",
        error: err instanceof ApiError ? err : new ApiError("Could not load the model settings."),
      }));
  }, []);

  useEffect(() => {
    reloadSchema();
  }, [reloadSchema]);

  useEffect(() => {
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
    } catch {
      /* the form still works without session storage */
    }
  }, [draft]);

  const updateDraft = useCallback((patch: Partial<AssessmentDraft>) => {
    setDraft((d) => ({ ...d, ...patch }));
  }, []);
  const resetDraft = useCallback(() => setDraft(EMPTY_DRAFT), []);

  const value = useMemo(
    () => ({ schemaState, reloadSchema, draft, updateDraft, resetDraft }),
    [schemaState, reloadSchema, draft, updateDraft, resetDraft],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAppState(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAppState must be used inside AppStateProvider");
  return ctx;
}
