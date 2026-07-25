export type DutyStatus =
  | "off_duty"
  | "sleeper_berth"
  | "driving"
  | "on_duty_not_driving";

export type EventKind =
  | "pre_trip_off_duty"
  | "driving"
  | "pickup"
  | "dropoff"
  | "fuel"
  | "break"
  | "daily_rest"
  | "cycle_restart"
  | "post_trip_off_duty";

export interface LocationCandidate {
  id: string;
  label: string;
  longitude: number;
  latitude: number;
  country_code: "US";
}

export interface TripPlanRequest {
  current_location: LocationCandidate;
  pickup_location: LocationCandidate;
  dropoff_location: LocationCandidate;
  current_cycle_used_hours: number;
  starts_at: string;
  home_terminal_timezone: string;
}

export interface DutyEvent {
  id: string;
  kind: EventKind;
  duty_status: DutyStatus;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  route_start_m: number;
  route_end_m: number;
  location: LocationCandidate;
  remark: string;
}

export interface RouteStep {
  instruction: string;
  road_name: string;
  distance_m: number;
  duration_minutes: number;
}

export interface DailyLogSegment {
  event_id: string;
  kind: EventKind;
  duty_status: DutyStatus;
  start_minute: number;
  end_minute: number;
  location: LocationCandidate;
  remark: string;
}

export interface DailyLog {
  date: string;
  trip_day: number;
  start_location: LocationCandidate;
  end_location: LocationCandidate;
  distance_m: number;
  totals_minutes: Record<DutyStatus, number>;
  cycle: {
    used_at_start_minutes: number;
    added_minutes: number;
    remaining_at_end_minutes: number;
  };
  segments: DailyLogSegment[];
}

export interface TripPlanResponse {
  meta: {
    generated_at: string;
    rule_set_version: string;
    home_terminal_timezone: string;
    fixed_utc_offset_minutes: number;
    assumptions: string[];
    warnings: string[];
  };
  summary: {
    starts_at: string;
    ends_at: string;
    distance_m: number;
    distance_miles: string;
    driving_minutes: number;
    on_duty_not_driving_minutes: number;
    off_duty_minutes: number;
    sleeper_berth_minutes: number;
    total_duration_minutes: number;
    cycle_used_start_minutes: number;
    cycle_used_end_minutes: number;
    cycle_restarts: number;
    log_days: number;
    fuel_stops: number;
    rest_stops: number;
  };
  route: {
    bounds: {
      west: number;
      south: number;
      east: number;
      north: number;
    };
    geometry: {
      type: "LineString";
      coordinates: [number, number][];
    };
    legs: {
      from: LocationCandidate;
      to: LocationCandidate;
      distance_m: number;
      duration_minutes: number;
      steps: RouteStep[];
    }[];
  };
  events: DutyEvent[];
  stops: DutyEvent[];
  daily_logs: DailyLog[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field: string | null;
    retryable: boolean;
  };
}
