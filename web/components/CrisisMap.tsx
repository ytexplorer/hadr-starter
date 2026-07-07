"use client";

import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { CrisisEvent } from "@/lib/contract.types";
import { markerRadius, severityColor } from "@/lib/presentation";

export function CrisisMap({
  events,
  selectedId,
  onSelect,
}: {
  events: CrisisEvent[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [mounted, setMounted] = useState(false);
  // SSR-safe mount gate: react-leaflet touches window/document, so render is deferred
  // until after hydration.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setMounted(true), []);
  if (!mounted) return <div data-testid="map-loading" style={{ height: "100%" }} />;

  return (
    <MapContainer center={[20, 0]} zoom={2} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      {events.map((e) => (
        <CircleMarker
          key={e.id}
          center={[e.geometry.lat, e.geometry.lon]}
          radius={markerRadius(e.magnitude)}
          pathOptions={{ color: severityColor(e.severity.level), weight: e.id === selectedId ? 4 : 1 }}
          eventHandlers={{ click: () => onSelect(e.id) }}
        >
          <Tooltip>{e.title}</Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
