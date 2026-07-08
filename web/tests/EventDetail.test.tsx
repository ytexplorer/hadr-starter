import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import example from "../../contract/fixtures/contract.v2.example.json";
import type { Contract } from "@/lib/contract.types";
import { feedLabel, formatAffected, hazardLabel } from "@/lib/presentation";
import { EventDetail } from "@/components/EventDetail";

const events = (example as Contract).events;
const severe = events[0]; // usgs:us6000severe — EQ, magnitude present, USGS-only, affected null
const cyclone = events[1]; // gdacs:1550421 — TC, magnitude null, affected set
const merged = events[2]; // usgs:us6000serious — EQ merged usgs+gdacs, boost applied, GDACS affected
const minor = events[3]; // usgs:us6000minor — non-major, boost.applied === 0, affected null

describe("EventDetail", () => {
  it("prompts to select when no event is given", () => {
    render(<EventDetail event={null} />);
    expect(screen.getByLabelText("event detail")).toHaveTextContent(/select an event/i);
  });

  it("shows the human hazard label, not the raw code", () => {
    render(<EventDetail event={cyclone} />);
    expect(screen.getByText(hazardLabel(cyclone.hazard))).toBeInTheDocument();
    expect(screen.queryByText(cyclone.hazard)).not.toBeInTheDocument();
  });

  it("shows the severity level and numeric score", () => {
    render(<EventDetail event={merged} />);
    const aside = screen.getByLabelText("event detail");
    expect(aside).toHaveTextContent(/score/i);
    expect(aside).toHaveTextContent(String(merged.severity.score));
    expect(screen.getByText(merged.severity.level)).toBeInTheDocument();
  });

  it("renders one source link per feed for a merged event", () => {
    render(<EventDetail event={merged} />);
    const usgs = merged.sources.find((s) => s.feed === "usgs")!;
    const gdacs = merged.sources.find((s) => s.feed === "gdacs")!;
    expect(screen.getAllByRole("link")).toHaveLength(merged.sources.length);
    expect(screen.getByRole("link", { name: new RegExp(feedLabel("usgs")) })).toHaveAttribute(
      "href",
      usgs.url,
    );
    expect(screen.getByRole("link", { name: new RegExp(feedLabel("gdacs")) })).toHaveAttribute(
      "href",
      gdacs.url,
    );
  });

  it("shows the boost-audit block with nearest place and distance", () => {
    render(<EventDetail event={merged} />);
    const why = screen.getByRole("region", { name: /why this ranks here/i });
    expect(why).toHaveTextContent(merged.severity.boost.nearest_place!);
    expect(why).toHaveTextContent(String(merged.severity.boost.distance_km));
  });

  it("shows the no-boost line without crashing when applied === 0", () => {
    render(<EventDetail event={minor} />);
    const why = screen.getByRole("region", { name: /why this ranks here/i });
    expect(why).toHaveTextContent(/no boost applied/i);
    expect(why).toHaveTextContent(minor.severity.boost.nearest_place!);
  });

  it("shows magnitude for an EQ and hides it for a TC", () => {
    const { unmount } = render(<EventDetail event={severe} />);
    expect(screen.getByText(/magnitude/i)).toBeInTheDocument();
    expect(screen.getByText(String(severe.magnitude))).toBeInTheDocument();
    unmount();
    render(<EventDetail event={cyclone} />);
    expect(screen.queryByText(/magnitude/i)).not.toBeInTheDocument();
  });

  it("shows a GDACS-tagged exposure estimate, and 'Not estimated' when null", () => {
    const { unmount } = render(<EventDetail event={merged} />);
    expect(screen.getByText(formatAffected(merged.affected))).toBeInTheDocument();
    const aside = screen.getByLabelText("event detail");
    expect(aside).toHaveTextContent(/GDACS/);
    expect(aside).toHaveTextContent(/population exposed/i);
    unmount();
    render(<EventDetail event={severe} />);
    expect(screen.getByText(/not estimated/i)).toBeInTheDocument();
  });
});
