import "leaflet/dist/leaflet.css";

import { latLngBounds } from "leaflet";
import { useEffect } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import { formatDateTime, formatDuration } from "@/lib/format";
import type { DutyEvent, TripPlanResponse } from "@/lib/api/types";

const STOP_COLORS: Record<string, string> = {
  current: "#7e8d80",
  pickup: "#e59a18",
  dropoff: "#365c4c",
  fuel: "#b76c19",
  break: "#58728a",
  daily_rest: "#182231",
  cycle_restart: "#7f4d82",
};

function FitRoute({ coordinates }: { coordinates: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    const bounds = latLngBounds(
      coordinates.map(([longitude, latitude]) => [latitude, longitude]),
    );
    map.fitBounds(bounds, { padding: [32, 32] });
  }, [coordinates, map]);
  return null;
}

interface Props {
  plan: TripPlanResponse;
  selectedEventId: string | null;
  onSelectEvent: (event: DutyEvent) => void;
}

export function RouteMap({
  plan,
  selectedEventId,
  onSelectEvent,
}: Props) {
  const positions = plan.route.geometry.coordinates.map(
    ([longitude, latitude]) => [latitude, longitude] as [number, number],
  );
  const current = plan.route.legs[0].from;
  const markers = [
    {
      id: "current-location",
      kind: "current",
      location: current,
      remark: "Current location",
      start_at: plan.summary.starts_at,
      duration_minutes: 0,
    },
    ...plan.stops,
  ];

  return (
    <section className="route-map-shell" aria-label="Planned route map">
      <MapContainer
        center={positions[0]}
        zoom={5}
        scrollWheelZoom
        className="route-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> · Routing by <a href="https://openrouteservice.org/">openrouteservice</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline
          positions={positions}
          pathOptions={{ color: "#182231", weight: 5 }}
        />
        {markers.map((marker) => (
          <CircleMarker
            key={marker.id}
            center={[marker.location.latitude, marker.location.longitude]}
            radius={selectedEventId === marker.id ? 10 : 7}
            pathOptions={{
              color: "#fffdf8",
              weight: 3,
              fillColor: STOP_COLORS[marker.kind] ?? "#182231",
              fillOpacity: 1,
            }}
            eventHandlers={{
              click: () => {
                if ("duty_status" in marker) onSelectEvent(marker);
              },
            }}
          >
            <Popup>
              <strong>{marker.remark}</strong>
              <span>{marker.location.label}</span>
              <span>
                {formatDateTime(marker.start_at)}
                {marker.duration_minutes
                  ? ` · ${formatDuration(marker.duration_minutes)}`
                  : ""}
              </span>
              {"duty_status" in marker && (
                <span>{marker.duty_status.replaceAll("_", " ")}</span>
              )}
            </Popup>
          </CircleMarker>
        ))}
        <FitRoute coordinates={plan.route.geometry.coordinates} />
      </MapContainer>
    </section>
  );
}
