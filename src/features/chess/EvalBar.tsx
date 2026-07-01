'use client';

/** Converts a White-perspective centipawn (or mate) score into a 0-100 "White share" of the bar. */
function toWhitePercent(cp: number | null, mate: number | null): number {
  if (mate !== null) {
    return mate > 0 ? 99 : 1;
  }
  if (cp === null) {
    return 50;
  }
  const winPercent = 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1);
  return Math.min(99, Math.max(1, winPercent));
}

export function EvalBar(props: {
  cp: number | null;
  mate: number | null;
  orientation?: 'w' | 'b';
}) {
  const whitePercent = toWhitePercent(props.cp, props.mate);
  const displayPercent = props.orientation === 'b' ? 100 - whitePercent : whitePercent;

  const label = props.mate !== null
    ? `M${Math.abs(props.mate)}`
    : props.cp !== null
      ? `${props.cp > 0 ? '+' : ''}${(props.cp / 100).toFixed(1)}`
      : '–';

  return (
    <div
      className="
        matrix-glow-border relative h-[560px] w-8 overflow-hidden rounded-md
        border-2 bg-[oklch(0.1_0.01_150)]
      "
    >
      <div
        className="
          absolute inset-x-0 bottom-0 bg-(--matrix-green) transition-[height]
          duration-500 ease-out
        "
        style={{ height: `${displayPercent}%` }}
      />
      <div
        className="
          absolute inset-x-0 bottom-1 text-center text-[10px] font-bold
          text-white [text-shadow:0_0_3px_black,0_0_3px_black]
        "
      >
        {label}
      </div>
    </div>
  );
}
