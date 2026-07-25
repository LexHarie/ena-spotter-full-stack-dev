interface Props {
  usedHours: number;
}

export function CycleMeter({ usedHours }: Props) {
  const safeUsed = Number.isFinite(usedHours)
    ? Math.min(70, Math.max(0, usedHours))
    : 0;
  const remaining = 70 - safeUsed;
  return (
    <div className="cycle-meter" aria-live="polite">
      <div>
        <span>{safeUsed.toFixed(2)} h used</span>
        <strong>{remaining.toFixed(2)} h available</strong>
      </div>
      <progress max={70} value={safeUsed} aria-label="Cycle hours used" />
    </div>
  );
}
