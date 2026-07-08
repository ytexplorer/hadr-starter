import type { CrisisEvent } from "@/lib/contract.types";
import { feedLabel, formatAffected, hazardLabel, severityColor } from "@/lib/presentation";
import { ProvisionalBadge } from "./ProvisionalBadge";

export function EventDetail({ event }: { event: CrisisEvent | null }) {
  if (!event) {
    return <aside aria-label="event detail">Select an event</aside>;
  }
  const { boost, level, score } = event.severity;
  return (
    <aside aria-label="event detail">
      <h2>{event.title}</h2>
      <dl>
        <dt>Hazard</dt>
        <dd>{hazardLabel(event.hazard)}</dd>
        <dt>Severity</dt>
        <dd>
          <span style={{ color: severityColor(level) }}>{level}</span>
          {" · score "}
          {score}
        </dd>
        {event.magnitude !== null && (
          <>
            <dt>Magnitude</dt>
            <dd>{event.magnitude}</dd>
          </>
        )}
        <dt>Location</dt>
        <dd>{event.place}</dd>
        <dt>Time</dt>
        <dd>{event.time}</dd>
        <dt>Population exposed</dt>
        <dd>
          <span>{formatAffected(event.affected)}</span>
          <small className="muted">{event.affected.basis}</small>
        </dd>
      </dl>
      <section aria-label="Why this ranks here">
        <h3>Why this ranks here</h3>
        {boost.applied === 0 ? (
          <p>
            nearest population center: {boost.nearest_place} ({boost.distance_km} km) — no boost
            applied
          </p>
        ) : (
          <p>
            +{boost.applied} boost from {boost.nearest_place} ({boost.distance_km} km · pop{" "}
            {boost.population?.toLocaleString()})
          </p>
        )}
      </section>
      <ProvisionalBadge provisional={event.provisional} />
      <ul aria-label="sources">
        {event.sources.map((s) => (
          <li key={`${s.feed}:${s.id}`}>
            <a href={s.url}>{feedLabel(s.feed)} source</a>
          </li>
        ))}
      </ul>
    </aside>
  );
}
