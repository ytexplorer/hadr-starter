import { describe, expect, it, vi, afterEach } from "vitest";
import example from "../../contract/fixtures/contract.v2.example.json";
import { loadContract } from "@/lib/contract";

afterEach(() => vi.restoreAllMocks());

describe("loadContract", () => {
  it("returns the parsed contract on a 2.0.0 body", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(example), { status: 200 })));
    const contract = await loadContract("/api/contract");
    expect(contract.schema_version).toBe("2.0.0");
    expect(contract.events.length).toBe(4);
  });

  it("rejects a stale 1.0.0 body with a loud schema mismatch", async () => {
    const stale = { ...example, schema_version: "1.0.0" };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(stale), { status: 200 })));
    await expect(loadContract("/api/contract")).rejects.toThrow(/schema mismatch/);
  });

  it("throws on a non-200 response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("boom", { status: 503 })));
    await expect(loadContract("/api/contract")).rejects.toThrow(/503/);
  });
});
