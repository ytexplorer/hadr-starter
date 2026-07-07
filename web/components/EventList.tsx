import type { CrisisEvent } from "@/lib/contract.types";
import { severityColor } from "@/lib/presentation";
import { ProvisionalBadge } from "./ProvisionalBadge";

export function EventList({
  events,
  selectedId,
  onSelect,
}: {
  events: CrisisEvent[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <ul aria-label="event list">
      {events.map((e) => (
        <li key={e.id}>
          <button type="button" aria-current={e.id === selectedId} onClick={() => onSelect(e.id)}>
            <span>{e.title}</span>
            <span style={{ color: severityColor(e.severity.level) }}>{e.severity.level}</span>
            <ProvisionalBadge provisional={e.provisional} />
          </button>
        </li>
      ))}
    </ul>
  );
}
