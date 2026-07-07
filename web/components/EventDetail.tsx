import type { CrisisEvent } from "@/lib/contract.types";
import { severityColor } from "@/lib/presentation";
import { ProvisionalBadge } from "./ProvisionalBadge";

export function EventDetail({ event }: { event: CrisisEvent | null }) {
  if (!event) {
    return <aside aria-label="event detail">Select an event</aside>;
  }
  return (
    <aside aria-label="event detail">
      <h2>{event.title}</h2>
      <dl>
        <dt>Hazard</dt>
        <dd>{event.hazard}</dd>
        <dt>Severity</dt>
        <dd style={{ color: severityColor(event.severity.level) }}>{event.severity.level}</dd>
        <dt>Location</dt>
        <dd>{event.place}</dd>
        <dt>Time</dt>
        <dd>{event.time}</dd>
      </dl>
      <ProvisionalBadge provisional={event.provisional} />
      <a href={event.sources[0].url}>USGS source</a>
    </aside>
  );
}
