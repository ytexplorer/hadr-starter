import { hazardLabel, severityColor } from "@/lib/presentation";

const HAZARDS = ["EQ", "TC", "FL", "VO", "DR"] as const;
const LEVELS = ["severe", "serious", "moderate", "minor"] as const;

export function MapLegend() {
  return (
    <div
      aria-label="map legend"
      style={{
        position: "absolute",
        right: "0.75rem",
        bottom: "0.75rem",
        zIndex: 1000,
        maxWidth: "12rem",
        padding: "0.5rem 0.625rem",
        borderRadius: "0.375rem",
        border: "1px solid currentColor",
        background: "var(--background)",
        color: "var(--foreground)",
        fontSize: "0.75rem",
        lineHeight: 1.4,
        opacity: 0.95,
      }}
    >
      <strong>Hazards</strong>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {HAZARDS.map((code) => (
          <li key={code}>
            <span style={{ fontWeight: 700, marginRight: "0.375rem" }}>{code}</span>
            <span>{hazardLabel(code)}</span>
          </li>
        ))}
      </ul>
      <strong>Severity</strong>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {LEVELS.map((level) => (
          <li key={level} style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
            <span
              data-testid="legend-swatch"
              data-color={severityColor(level)}
              style={{
                display: "inline-block",
                width: "0.75rem",
                height: "0.75rem",
                borderRadius: "50%",
                background: severityColor(level),
              }}
            />
            <span>{level}</span>
          </li>
        ))}
      </ul>
      <p style={{ margin: "0.375rem 0 0" }}>Marker size &#8733; newsworthiness score</p>
    </div>
  );
}
