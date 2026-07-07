import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import noMajor from "../../contract/fixtures/contract.v1.no-major.json";
import feedDown from "../../contract/fixtures/contract.v1.feed-down.json";

// vi.mock factories are hoisted above top-level const declarations, so the mock fn
// must be created via vi.hoisted to avoid a TDZ ReferenceError at runtime.
const { loadContract } = vi.hoisted(() => ({ loadContract: vi.fn() }));
vi.mock("@/lib/contract", () => ({ loadContract, CONTRACT_URL: "/api/contract" }));

// Stub next/dynamic so the map is a black box here (its own test covers it).
/* eslint-disable @typescript-eslint/no-explicit-any -- mock props mirror next/dynamic's own loosely-typed component props */
vi.mock("next/dynamic", () => ({
  default: () => (props: any) => <div data-testid="map-stub" data-count={props.events.length} />,
}));
/* eslint-enable @typescript-eslint/no-explicit-any */

import Page from "@/app/page";

afterEach(() => vi.clearAllMocks());

describe("dashboard page", () => {
  it("renders map + list from the contract, major-only, with no key", async () => {
    loadContract.mockResolvedValue(example);
    render(<Page />);
    await screen.findByLabelText("event list");
    expect(screen.getAllByRole("button").length).toBe(2); // 2 major events, no key entry anywhere
    expect(screen.getByTestId("map-stub")).toHaveAttribute("data-count", "2");
  });

  it("syncs selection: clicking a list row fills the detail card", async () => {
    loadContract.mockResolvedValue(example);
    render(<Page />);
    await userEvent.click(await screen.findByText(/M 6.0/));
    expect(screen.getByLabelText("event detail")).toHaveTextContent(/12 km S of Sampletown/);
  });

  it("shows 'no major events' when the default view is empty", async () => {
    loadContract.mockResolvedValue(noMajor);
    render(<Page />);
    expect(await screen.findByText(/no major events/i)).toBeInTheDocument();
  });

  it("shows an outage banner when a feed errored", async () => {
    loadContract.mockResolvedValue(feedDown);
    render(<Page />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/USGS unavailable/i);
  });

  it("shows an error state when the contract fails to load", async () => {
    loadContract.mockRejectedValue(new Error("503"));
    render(<Page />);
    await waitFor(() => expect(screen.getByText(/failed to load/i)).toBeInTheDocument());
  });
});
