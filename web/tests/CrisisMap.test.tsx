import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import type { Contract } from "@/lib/contract.types";

/* eslint-disable @typescript-eslint/no-explicit-any -- mock props mirror react-leaflet's own loosely-typed component props */
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: any) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Tooltip: ({ children }: any) => <span>{children}</span>,
  CircleMarker: ({ center, radius, pathOptions, eventHandlers, children }: any) => (
    <button
      data-testid="marker"
      data-lat={center[0]}
      data-lon={center[1]}
      data-radius={radius}
      data-color={pathOptions.color}
      data-weight={pathOptions.weight}
      onClick={eventHandlers.click}
    >
      {children}
    </button>
  ),
}));
/* eslint-enable @typescript-eslint/no-explicit-any */

import { CrisisMap } from "@/components/CrisisMap";

const events = (example as Contract).events.filter((e) => e.major);

describe("CrisisMap", () => {
  it("renders one marker per event, coloured by severity", async () => {
    render(<CrisisMap events={events} selectedId={null} onSelect={() => {}} />);
    const markers = await screen.findAllByTestId("marker");
    expect(markers.length).toBe(2);
    expect(markers[0]).toHaveAttribute("data-color", "#dc2626"); // severe
  });

  it("thickens the selected marker's stroke", async () => {
    render(<CrisisMap events={events} selectedId="usgs:us6000severe" onSelect={() => {}} />);
    const selected = (await screen.findAllByTestId("marker")).find(
      (m) => m.getAttribute("data-lat") === "-19.1",
    );
    expect(Number(selected?.getAttribute("data-weight"))).toBeGreaterThan(1);
  });

  it("calls onSelect when a marker is clicked", async () => {
    const onSelect = vi.fn();
    render(<CrisisMap events={events} selectedId={null} onSelect={onSelect} />);
    await userEvent.click((await screen.findAllByTestId("marker"))[0]);
    expect(onSelect).toHaveBeenCalledWith("usgs:us6000severe");
  });
});
