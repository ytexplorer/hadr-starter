import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import type { Contract } from "@/lib/contract.types";
import { EventDetail } from "@/components/EventDetail";

const severe = (example as Contract).events[0];

describe("EventDetail", () => {
  it("prompts to select when no event is given", () => {
    render(<EventDetail event={null} />);
    expect(screen.getByLabelText("event detail")).toHaveTextContent(/select an event/i);
  });

  it("shows title, hazard, severity, location, time, source link, provisional badge", () => {
    render(<EventDetail event={severe} />);
    expect(screen.getByRole("heading")).toHaveTextContent(/M 7.1/);
    expect(screen.getByText("EQ")).toBeInTheDocument();
    expect(screen.getByText("severe")).toBeInTheDocument();
    expect(screen.getByText("40 km W of Testville")).toBeInTheDocument(); // exact match: place is a substring of the title, so a regex would match both
    expect(screen.getByRole("link", { name: /source/i })).toHaveAttribute(
      "href",
      "https://earthquake.usgs.gov/earthquakes/eventpage/us6000severe",
    );
    expect(screen.getByTestId("provisional-badge")).toBeInTheDocument();
  });
});
