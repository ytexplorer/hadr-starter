import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import example from "../../contract/fixtures/contract.v2.example.json";
import type { Contract } from "@/lib/contract.types";
import { markerRadius, severityColor } from "@/lib/presentation";

/* eslint-disable @typescript-eslint/no-explicit-any -- mock props mirror react-leaflet's / leaflet's own loosely-typed props */
vi.mock("leaflet", () => ({
  divIcon: (opts: any) => ({ options: opts }),
}));

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: any) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  Tooltip: ({ children }: any) => <span>{children}</span>,
  Marker: ({ position, icon, eventHandlers }: any) => (
    <button
      data-testid="marker"
      data-lat={position[0]}
      data-lon={position[1]}
      onClick={eventHandlers.click}
      dangerouslySetInnerHTML={{ __html: icon.options.html }}
    />
  ),
}));
/* eslint-enable @typescript-eslint/no-explicit-any */

import { CrisisMap } from "@/components/CrisisMap";

const major = (example as Contract).events.filter((e) => e.major);

describe("CrisisMap", () => {
  it("renders one marker per event with the hazard glyph and level colour, in order", async () => {
    render(<CrisisMap events={major} selectedId={null} onSelect={() => {}} />);
    const markers = await screen.findAllByTestId("marker");
    expect(markers).toHaveLength(major.length);
    const rendered = markers.map((m) => {
      const badge = m.querySelector("[data-color]") as HTMLElement;
      return { glyph: badge.textContent, color: badge.getAttribute("data-color") };
    });
    const expected = major.map((e) => ({
      glyph: e.hazard,
      color: severityColor(e.severity.level),
    }));
    expect(rendered).toEqual(expected);
  });

  it("sizes each marker from severity.score", async () => {
    render(<CrisisMap events={major} selectedId={null} onSelect={() => {}} />);
    const markers = await screen.findAllByTestId("marker");
    markers.forEach((m, i) => {
      const badge = m.querySelector("[data-color]") as HTMLElement;
      expect(badge.getAttribute("data-size")).toBe(String(markerRadius(major[i].severity.score)));
    });
  });

  it("marks the selected event with the ring class and leaves others unringed", async () => {
    render(<CrisisMap events={major} selectedId="gdacs:1550421" onSelect={() => {}} />);
    await screen.findAllByTestId("marker");
    expect(screen.getByText("TC").className).toContain("crisis-marker--selected");
    expect(screen.getAllByText("EQ")[0].className).not.toContain("crisis-marker--selected");
  });

  it("calls onSelect with the event id when a marker is clicked", async () => {
    const onSelect = vi.fn();
    render(<CrisisMap events={major} selectedId={null} onSelect={onSelect} />);
    const markers = await screen.findAllByTestId("marker");
    await userEvent.click(markers[0]);
    expect(onSelect).toHaveBeenCalledWith(major[0].id);
  });
});
