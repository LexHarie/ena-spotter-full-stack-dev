import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { CycleMeter } from "@/components/planner/CycleMeter";
import { LocationCombobox } from "@/components/planner/LocationCombobox";
import { Button } from "@/components/ui/button";
import type { ApiClientError } from "@/lib/api/client";
import type { LocationCandidate, TripPlanRequest } from "@/lib/api/types";
import { getTripStartContext } from "@/lib/time";

const locationSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  longitude: z.number(),
  latitude: z.number(),
  country_code: z.literal("US"),
});

const formSchema = z.object({
  current_location: locationSchema
    .nullable()
    .refine(Boolean, "Select a current location."),
  pickup_location: locationSchema
    .nullable()
    .refine(Boolean, "Select a pickup location."),
  dropoff_location: locationSchema
    .nullable()
    .refine(Boolean, "Select a drop-off location."),
  current_cycle_used_hours: z
    .number({ error: "Enter current cycle usage." })
    .min(0, "Cycle usage cannot be negative.")
    .max(70, "Cycle usage cannot exceed 70 hours.")
    .refine(
      (value) => Number.isInteger(value * 4),
      "Use quarter-hour increments.",
    ),
});

type FormInput = z.input<typeof formSchema>;
type FormValues = z.output<typeof formSchema>;

interface Props {
  onPlan: (request: TripPlanRequest) => void;
  isPlanning: boolean;
  serverError?: ApiClientError | null;
}

export function TripForm({ onPlan, isPlanning, serverError }: Props) {
  const {
    control,
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormInput, unknown, FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      current_location: null,
      pickup_location: null,
      dropoff_location: null,
      current_cycle_used_hours: 0,
    },
  });
  const cycleUsed = Number(watch("current_cycle_used_hours"));
  const fieldError = (name: keyof FormValues) =>
    errors[name]?.message ??
    (serverError?.field === name ? serverError.message : undefined);
  const cycleError = fieldError("current_cycle_used_hours");

  const submit = (values: FormValues) => {
    const context = getTripStartContext();
    onPlan({
      current_location: values.current_location as LocationCandidate,
      pickup_location: values.pickup_location as LocationCandidate,
      dropoff_location: values.dropoff_location as LocationCandidate,
      current_cycle_used_hours: values.current_cycle_used_hours,
      ...context,
    });
  };

  return (
    <form
      className="trip-form"
      onSubmit={handleSubmit(submit)}
      aria-busy={isPlanning}
      noValidate
    >
      {(
        [
          ["current_location", "Current location"],
          ["pickup_location", "Pickup location"],
          ["dropoff_location", "Drop-off location"],
        ] as const
      ).map(([name, label]) => (
        <Controller
          key={name}
          name={name}
          control={control}
          render={({ field }) => (
            <LocationCombobox
              id={name}
              label={label}
              value={field.value}
              onChange={field.onChange}
              error={fieldError(name)}
            />
          )}
        />
      ))}
      <div className="field-group">
        <label htmlFor="current_cycle_used_hours">
          Current cycle used (hours)
        </label>
        <input
          id="current_cycle_used_hours"
          type="number"
          min="0"
          max="70"
          step="0.25"
          aria-invalid={Boolean(cycleError)}
          aria-describedby={
            cycleError ? "current-cycle-used-error" : undefined
          }
          {...register("current_cycle_used_hours", { valueAsNumber: true })}
        />
        {cycleError && (
          <p
            id="current-cycle-used-error"
            role="alert"
            className="field-error"
          >
            {cycleError}
          </p>
        )}
      </div>
      <CycleMeter usedHours={cycleUsed} />
      <a className="assumptions-link" href="#planning-assumptions">
        Review planning assumptions
      </a>
      <Button type="submit" disabled={isPlanning}>
        {isPlanning ? "Building trip plan…" : "Build trip plan"}
        <ArrowRight aria-hidden="true" size={16} />
      </Button>
    </form>
  );
}
