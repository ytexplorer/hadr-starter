import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import type { Contract } from "@/lib/contract.types";
import { EventList } from "@/components/EventList";

const events = (example as Contract).events.filter((e) => e.major);

describe("EventList", () => {
  it("renders one row per event with its title", () => {
    render(<EventList events={events} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText(/M 7.1/)).toBeInTheDocument();
    expect(screen.getByText(/M 6.0/)).toBeInTheDocument();
  });

  it("badges provisional events only", () => {
    render(<EventList events={events} selectedId={null} onSelect={() => {}} />);
    expect(screen.getAllByTestId("provisional-badge").length).toBe(1);
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
