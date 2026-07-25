import { useEffect, useState } from "react";

import { ApiClientError, searchLocations } from "@/lib/api/client";
import type { LocationCandidate } from "@/lib/api/types";

export function useLocationSearch(query: string) {
  const [options, setOptions] = useState<LocationCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 3) {
      setOptions([]);
      setLoading(false);
      setError(null);
      return;
    }
    setOptions([]);
    setLoading(true);
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setError(null);
      try {
        const results = await searchLocations(trimmed, controller.signal);
        if (!controller.signal.aborted) setOptions(results);
      } catch (caught) {
        if (controller.signal.aborted) return;
        setError(
          caught instanceof ApiClientError
            ? caught.message
            : "Location search is unavailable.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 300);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [query]);

  return { options, loading, error };
}
