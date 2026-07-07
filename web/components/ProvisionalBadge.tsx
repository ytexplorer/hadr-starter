export function ProvisionalBadge({ provisional }: { provisional: boolean }) {
  if (!provisional) return null;
  return (
    <span data-testid="provisional-badge" title="Unreviewed automatic solution" className="badge">
      provisional
    </span>
  );
}
