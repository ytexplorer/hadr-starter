import { describe, expect, it, vi, afterEach } from "vitest";
import example from "../../contract/fixtures/contract.v1.example.json";
import { loadContract } from "@/lib/contract";

afterEach(() => vi.restoreAllMocks());

describe("loadContract", () => {
  it("returns the parsed contract on 200", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(example), { status: 200 })));
    const contract = await loadContract("/api/contract");
    expect(contract.schema_version).toBe("1.0.0");
    expect(contract.events.length).toBe(3);
  });

  it("throws on a non-200 response", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("boom", { status: 503 })));
    await expect(loadContract("/api/contract")).rejects.toThrow(/503/);
  });
});
