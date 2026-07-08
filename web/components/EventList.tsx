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
            <span data-testid="hazard-glyph" className="glyph" aria-hidden>
              {e.hazard}
            </span>
            <span>{e.title}</span>
            <span style={{ color: severityColor(e.severity.level) }}>{e.severity.level}</span>
            <span data-testid="event-score">{Math.round(e.severity.score)}</span>
            <ProvisionalBadge provisional={e.provisional} />
            {e.sources.length > 1 && (
              <span
                data-testid="multi-source-badge"
                className="badge"
                title="Reported by multiple feeds"
              >
                multi-source
              </span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
