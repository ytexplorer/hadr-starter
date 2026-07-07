import type { Contract, CrisisEvent, Severity } from "./contract.types";

const COLORS: Record<Severity["level"], string> = {
  severe: "#dc2626",
  serious: "#ea580c",
  moderate: "#ca8a04",
  minor: "#6b7280",
};

export function severityColor(level: Severity["level"]): string {
  return COLORS[level];
}

export function markerRadius(magnitude: number): number {
  return Math.max(4, Math.round((magnitude - 2) * 3));
}

export function defaultMajorEvents(contract: Contract): CrisisEvent[] {
  return contract.events.filter((e) => e.major);
}

export function feedsDown(contract: Contract): boolean {
  return contract.meta.feeds.some((f) => f.status === "error");
}
