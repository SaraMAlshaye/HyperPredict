import { Button } from "../components/Button";
import { EmptyState } from "../components/States";

export function NotFound() {
  return (
    <div className="page">
      <EmptyState title="Page not found" message="Pulsie looked everywhere, but this page doesn't exist."
                  action={<Button to="/" icon="home">Back to home</Button>} />
    </div>
  );
}
