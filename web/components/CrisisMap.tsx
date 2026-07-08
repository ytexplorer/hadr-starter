"use client";

import { useEffect, useState } from "react";
import { MapContainer, Marker, TileLayer, Tooltip } from "react-leaflet";
import { divIcon } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { CrisisEvent } from "@/lib/contract.types";
import { markerRadius, severityColor } from "@/lib/presentation";

// SSR-safe HTML badge: colour = level, size = markerRadius(score), 2-letter hazard glyph,
// ring when selected. All styling inline so no image asset or stylesheet is required.
function markerBadge(e: CrisisEvent, selected: boolean, size: number): string {
  const color = severityColor(e.severity.level);
  const cls = selected ? "crisis-marker crisis-marker--selected" : "crisis-marker";
  const ring = selected ? `box-shadow:0 0 0 2px #ffffff,0 0 0 5px ${color};` : "";
  return `<div class="${cls}" data-color="${color}" data-size="${size}" style="width:${size}px;height:${size}px;line-height:${size}px;border-radius:50%;background:${color};color:#ffffff;font-size:${Math.max(8, Math.round(size * 0.5))}px;font-weight:700;text-align:center;border:1px solid #ffffff;${ring}">${e.hazard}</div>`;
}

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
      {events.map((e) => {
        const selected = e.id === selectedId;
        const size = markerRadius(e.severity.score);
        const icon = divIcon({
          html: markerBadge(e, selected, size),
          className: "crisis-marker-icon",
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        });
        return (
          <Marker
            key={e.id}
            position={[e.geometry.lat, e.geometry.lon]}
            icon={icon}
            eventHandlers={{ click: () => onSelect(e.id) }}
          >
            <Tooltip>{e.title}</Tooltip>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
