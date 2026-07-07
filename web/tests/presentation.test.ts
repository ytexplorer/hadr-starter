import { describe, expect, it } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import feedDown from "../../contract/fixtures/contract.v1.feed-down.json";
import type { Contract } from "@/lib/contract.types";
import { defaultMajorEvents, feedsDown, markerRadius, severityColor } from "@/lib/presentation";

describe("presentation helpers", () => {
  it("maps every severity level to a distinct colour", () => {
    const colours = new Set(["minor", "moderate", "serious", "severe"].map((l) => severityColor(l as never)));
    expect(colours.size).toBe(4);
  });

  it("grows marker radius with magnitude and clamps a floor", () => {
    expect(markerRadius(7.1)).toBeGreaterThan(markerRadius(4.0));
    expect(markerRadius(0)).toBeGreaterThanOrEqual(4);
  });

  it("default view keeps only major events", () => {
    const majors = defaultMajorEvents(example as Contract);
    expect(majors.length).toBe(2);
    expect(majors.every((e) => e.major)).toBe(true);
  });

  it("detects feed outages from meta", () => {
    expect(feedsDown(example as Contract)).toBe(false);
    expect(feedsDown(feedDown as Contract)).toBe(true);
  });
});
