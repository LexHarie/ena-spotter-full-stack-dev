import { RotateCcw } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ApiClientError } from "@/lib/api/client";

export function ErrorAlert({
  error,
  onRetry,
}: {
  error: ApiClientError;
  onRetry: () => void;
}) {
  return (
    <Alert title="We could not build this route.">
      <p>{error.message}</p>
      {error.retryable && (
        <Button type="button" variant="quiet" onClick={onRetry}>
          <RotateCcw aria-hidden="true" size={15} />
          Retry
        </Button>
      )}
    </Alert>
  );
}
