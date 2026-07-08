import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import example from "../../contract/fixtures/contract.v2.example.json";
import type { Contract } from "@/lib/contract.types";
import { EventList } from "@/components/EventList";

const events = (example as Contract).events.filter((e) => e.major);

describe("EventList", () => {
  it("renders one row per major event with title, hazard glyph, and score", () => {
    render(<EventList events={events} selectedId={null} onSelect={() => {}} />);

    expect(screen.getAllByRole("button")).toHaveLength(events.length);
    expect(screen.getByText(/M 7.1/)).toBeInTheDocument();
    expect(screen.getByText(/M 6.0/)).toBeInTheDocument();

    const glyphs = screen.getAllByTestId("hazard-glyph").map((el) => el.textContent);
    expect(glyphs).toEqual(events.map((e) => e.hazard));

    const scores = screen.getAllByTestId("event-score").map((el) => el.textContent);
    expect(scores).toEqual(events.map((e) => String(Math.round(e.severity.score))));
  });

  it("shows the multi-source badge only on the merged (multi-source) event", () => {
    render(<EventList events={events} selectedId={null} onSelect={() => {}} />);

    const merged = events.filter((e) => e.sources.length > 1);
    const single = events.filter((e) => e.sources.length === 1);
    expect(screen.getAllByTestId("multi-source-badge")).toHaveLength(merged.length);

    const mergedRow = screen.getByText(merged[0].title).closest("button") as HTMLElement;
    expect(within(mergedRow).queryByTestId("multi-source-badge")).toBeInTheDocument();

    const singleRow = screen.getByText(single[0].title).closest("button") as HTMLElement;
    expect(within(singleRow).queryByTestId("multi-source-badge")).not.toBeInTheDocument();
  });

  it("badges provisional events only", () => {
    render(<EventList events={events} selectedId={null} onSelect={() => {}} />);
    const expected = events.filter((e) => e.provisional).length;
    expect(screen.queryAllByTestId("provisional-badge")).toHaveLength(expected);
  });

  it("calls onSelect with the event id when a row is clicked", async () => {
    const onSelect = vi.fn();
    render(<EventList events={events} selectedId={null} onSelect={onSelect} />);
    await userEvent.click(screen.getByText(/M 7.1/));
    expect(onSelect).toHaveBeenCalledWith("usgs:us6000severe");
  });

  it("marks the selected row via aria-current", () => {
    render(<EventList events={events} selectedId="usgs:us6000serious" onSelect={() => {}} />);
    expect(screen.getByRole("button", { current: true })).toHaveTextContent(/M 6.0/);
  });
});
