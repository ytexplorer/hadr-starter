import { describe, expect, it } from "vitest";
import example from "../../contract/fixtures/contract.v2.example.json";
import feedDown from "../../contract/fixtures/contract.v2.feed-down.json";
import type { Contract } from "@/lib/contract.types";
import {
  defaultMajorEvents,
  downFeeds,
  feedLabel,
  formatAffected,
  hazardLabel,
  markerRadius,
  severityColor,
} from "@/lib/presentation";

describe("presentation helpers", () => {
  it("maps every severity level to a distinct colour", () => {
    const colours = new Set(
      ["minor", "moderate", "serious", "severe"].map((l) => severityColor(l as never)),
    );
    expect(colours.size).toBe(4);
  });

  it("sizes markers off score: monotonic, floor 4, cap 22, handles 0", () => {
    expect(markerRadius(0)).toBe(4);
    expect(markerRadius(6.0)).toBeGreaterThan(markerRadius(0));
    expect(markerRadius(71.3)).toBeGreaterThan(markerRadius(6.0));
    expect(markerRadius(1000)).toBe(22);
  });

  it("labels hazards (5 distinct) with a raw-code fallback", () => {
    expect(hazardLabel("EQ")).toBe("Earthquake");
    expect(hazardLabel("TC")).toBe("Tropical Cyclone");
    expect(hazardLabel("FL")).toBe("Flood");
    expect(hazardLabel("VO")).toBe("Volcano");
    expect(hazardLabel("DR")).toBe("Drought");
    expect(new Set(["EQ", "TC", "FL", "VO", "DR"].map(hazardLabel)).size).toBe(5);
    expect(hazardLabel("WF")).toBe("WF");
  });

  it("labels feeds", () => {
    expect(feedLabel("usgs")).toBe("USGS");
    expect(feedLabel("gdacs")).toBe("GDACS");
  });

  it("returns the source codes of feeds in error", () => {
    expect(downFeeds(example as Contract)).toEqual([]);
    expect(downFeeds(feedDown as Contract)).toEqual(["gdacs"]);
  });

  it("formats the affected estimate for both branches", () => {
    expect(
      formatAffected({ estimate: 43996, basis: "40 thousand in MMI IV", source: "gdacs" }),
    ).toBe("Est. population exposed ≈ 44K · GDACS");
    expect(
      formatAffected({ estimate: null, basis: "no exposure figure for USGS-only event", source: null }),
    ).toBe("Not estimated — no exposure figure for USGS-only event");
  });

  it("keeps only major events, preserving contract order", () => {
    const majors = defaultMajorEvents(example as Contract);
    expect(majors.length).toBe(3);
    expect(majors.every((e) => e.major)).toBe(true);
    expect(majors.map((e) => e.id)).toEqual(
      (example as Contract).events.filter((e) => e.major).map((e) => e.id),
    );
  });
});
