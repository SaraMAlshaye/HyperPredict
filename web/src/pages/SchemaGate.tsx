import type { ReactNode } from "react";
import { ErrorState, LoadingState } from "../components/States";
import { useAppState } from "../lib/AppState";
import type { ModelSchema } from "../lib/types";

/** Renders children only once the model's schema has loaded from the backend. */
export function SchemaGate({ children }: { children: (schema: ModelSchema) => ReactNode }) {
  const { schemaState, reloadSchema } = useAppState();
  if (schemaState.status === "loading") return <LoadingState message="Connecting to the HyperPredict model…" />;
  if (schemaState.status === "error") {
    return (
      <ErrorState
        title="We can't reach the model"
        message={schemaState.error.message}
        details={schemaState.error.details}
        onRetry={reloadSchema}
      />
    );
  }
  return <>{children(schemaState.schema)}</>;
}
