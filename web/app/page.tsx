"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { EventDetail } from "@/components/EventDetail";
import { EventList } from "@/components/EventList";
import type { Contract } from "@/lib/contract.types";
import { loadContract } from "@/lib/contract";
import { defaultMajorEvents, feedsDown } from "@/lib/presentation";

const CrisisMap = dynamic(() => import("@/components/CrisisMap").then((m) => m.CrisisMap), {
  ssr: false,
});

export default function Page() {
  const [contract, setContract] = useState<Contract | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    loadContract()
      .then(setContract)
      .catch((e: unknown) => setError(String(e)));
  }, []);

  if (error) return <main>Failed to load the crisis picture: {error}</main>;
  if (!contract) return <main>Loading…</main>;

  const visible = defaultMajorEvents(contract);
  const selected = visible.find((e) => e.id === selectedId) ?? null;

  return (
    <main>
      {feedsDown(contract) && (
        <div role="alert">USGS unavailable — picture may be incomplete.</div>
      )}
      <p>Last updated {contract.generated_at}</p>
      <div className="dashboard">
        <div className="map-pane">
          <CrisisMap events={visible} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
        <div className="side-pane">
          {visible.length === 0 ? (
            <p>No major events right now.</p>
          ) : (
            <EventList events={visible} selectedId={selectedId} onSelect={setSelectedId} />
          )}
          <EventDetail event={selected} />
        </div>
      </div>
    </main>
  );
}
