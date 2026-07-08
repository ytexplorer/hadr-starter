import type { Contract } from "./contract.types";

export const CONTRACT_URL = process.env.NEXT_PUBLIC_CONTRACT_URL ?? "/api/contract";
export const EXPECTED_SCHEMA_VERSION = "2.0.0";

export async function loadContract(url: string = CONTRACT_URL): Promise<Contract> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`contract fetch failed: ${res.status}`);
  const data = (await res.json()) as Contract;
  if (data.schema_version !== EXPECTED_SCHEMA_VERSION) {
    throw new Error(
      "contract schema mismatch: expected " + EXPECTED_SCHEMA_VERSION + ", got " + data.schema_version,
    );
  }
  return data;
}
