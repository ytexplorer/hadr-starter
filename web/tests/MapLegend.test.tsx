import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MapLegend } from "@/components/MapLegend";
import { hazardLabel } from "@/lib/presentation";

describe("MapLegend", () => {
  it("lists all five hazard labels", () => {
    render(<MapLegend />);
    for (const code of ["EQ", "TC", "FL", "VO", "DR"] as const) {
      expect(screen.getByText(hazardLabel(code))).toBeInTheDocument();
    }
  });

  it("shows four severity colour swatches", () => {
    render(<MapLegend />);
    expect(screen.getAllByTestId("legend-swatch")).toHaveLength(4);
  });

  it("notes that marker size encodes newsworthiness", () => {
    render(<MapLegend />);
    expect(screen.getByText(/newsworthiness score/i)).toBeInTheDocument();
  });
});
