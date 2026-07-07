import type { Contract } from "./contract.types";

export const CONTRACT_URL = process.env.NEXT_PUBLIC_CONTRACT_URL ?? "/api/contract";

export async function loadContract(url: string = CONTRACT_URL): Promise<Contract> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`contract fetch failed: ${res.status}`);
  return (await res.json()) as Contract;
}
