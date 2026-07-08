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

export function markerRadius(score: number): number {
  return Math.max(4, Math.min(22, Math.round(4 + score * 0.18)));
}

const HAZARD_LABELS: Record<string, string> = {
  EQ: "Earthquake",
  TC: "Tropical Cyclone",
  FL: "Flood",
  VO: "Volcano",
  DR: "Drought",
};

export function hazardLabel(hazard: string): string {
  return HAZARD_LABELS[hazard] ?? hazard;
}

const FEED_LABELS: Record<string, string> = {
  usgs: "USGS",
  gdacs: "GDACS",
};

export function feedLabel(feed: string): string {
  return FEED_LABELS[feed] ?? feed;
}

export function downFeeds(contract: Contract): string[] {
  const seen = new Set<string>();
  for (const f of contract.meta.feeds) {
    if (f.status === "error") seen.add(f.source);
  }
  return [...seen];
}

function abbreviatePopulation(n: number): string {
  if (n >= 1_000_000) return `${Math.round(n / 1_000_000)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}K`;
  return `${n}`;
}

export function formatAffected(affected: CrisisEvent["affected"]): string {
  if (affected.estimate === null) {
    return `Not estimated — ${affected.basis}`;
  }
  const count = abbreviatePopulation(affected.estimate);
  const source = affected.source ? feedLabel(affected.source) : "";
  return `Est. population exposed ≈ ${count} · ${source}`;
}

export function defaultMajorEvents(contract: Contract): CrisisEvent[] {
  return contract.events.filter((e) => e.major);
}
