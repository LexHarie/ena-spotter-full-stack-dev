import { Command } from "cmdk";
import { MapPin, Search } from "lucide-react";
import { useState } from "react";

import { useLocationSearch } from "@/hooks/useLocationSearch";
import type { LocationCandidate } from "@/lib/api/types";

interface Props {
  id: string;
  label: string;
  value: LocationCandidate | null;
  onChange: (location: LocationCandidate | null) => void;
  error?: string;
}

export function LocationCombobox({
  id,
  label,
  value,
  onChange,
  error,
}: Props) {
  const [query, setQuery] = useState(value?.label ?? "");
  const { options, loading, error: searchError } = useLocationSearch(query);
  const open = query.trim().length >= 3 && query !== value?.label;

  return (
    <div className="field-group">
      <label htmlFor={id}>{label}</label>
      <Command
        label={label}
        shouldFilter={false}
        className="location-command"
      >
        <div className="location-input-wrap">
          <Search aria-hidden="true" size={16} />
          <Command.Input
            id={id}
            value={query}
            onValueChange={(nextQuery) => {
              setQuery(nextQuery);
              if (nextQuery !== value?.label) onChange(null);
            }}
            aria-invalid={Boolean(error)}
            aria-describedby={error || searchError ? `${id}-error` : undefined}
            placeholder="City, state, or address"
          />
        </div>
        {open && (
          <Command.List aria-label={`${label} suggestions`}>
            {loading && <Command.Loading>Searching…</Command.Loading>}
            {!loading && options.length === 0 && (
              <Command.Empty>No United States locations found.</Command.Empty>
            )}
            {options.map((option) => (
              <Command.Item
                key={option.id}
                value={option.id}
                onSelect={() => {
                  onChange(option);
                  setQuery(option.label);
                }}
              >
                <MapPin aria-hidden="true" size={15} />
                {option.label}
              </Command.Item>
            ))}
          </Command.List>
        )}
      </Command>
      {(error || searchError) && (
        <p id={`${id}-error`} role="alert" className="field-error">
          {error ?? searchError}
        </p>
      )}
    </div>
  );
}
