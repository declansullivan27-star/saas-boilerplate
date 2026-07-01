'use client';

import type { AnalyzedMove } from '@/features/chess/types';
import { CLASSIFICATION_COLOR, CLASSIFICATION_SYMBOL } from '@/features/chess/classificationStyles';
import { cn } from '@/utils/Helpers';

export function MoveList(props: {
  moves: AnalyzedMove[];
  currentPly: number;
  onSelect: (ply: number) => void;
}) {
  const pairs: { moveNumber: number; white?: AnalyzedMove; black?: AnalyzedMove }[] = [];
  for (const move of props.moves) {
    let pair = pairs.find(p => p.moveNumber === move.moveNumber);
    if (!pair) {
      pair = { moveNumber: move.moveNumber };
      pairs.push(pair);
    }
    if (move.color === 'w') {
      pair.white = move;
    } else {
      pair.black = move;
    }
  }

  return (
    <div className="
      matrix-panel h-[280px] overflow-y-auto rounded-md p-2 text-sm
    "
    >
      {pairs.map(pair => (
        <div
          key={pair.moveNumber}
          className="grid grid-cols-[2rem_1fr_1fr] gap-1 py-0.5"
        >
          <span className="text-[oklch(0.5_0.03_150)]">{pair.moveNumber}</span>
          <MoveCell move={pair.white} currentPly={props.currentPly} onSelect={props.onSelect} />
          <MoveCell move={pair.black} currentPly={props.currentPly} onSelect={props.onSelect} />
        </div>
      ))}
    </div>
  );
}

function MoveCell(props: {
  move: AnalyzedMove | undefined;
  currentPly: number;
  onSelect: (ply: number) => void;
}) {
  if (!props.move) {
    return <span />;
  }

  const isActive = props.move.ply === props.currentPly;

  return (
    <button
      type="button"
      onClick={() => props.onSelect(props.move!.ply)}
      className={cn(
        `
          flex items-center gap-1 rounded-sm px-1 text-left
          hover:bg-[oklch(0.25_0.02_150)]
        `,
        isActive && 'matrix-glow-text bg-[oklch(0.28_0.05_150)]',
      )}
    >
      <span>{props.move.san}</span>
      <span className={cn('text-xs', CLASSIFICATION_COLOR[props.move.classification])}>
        {CLASSIFICATION_SYMBOL[props.move.classification]}
      </span>
    </button>
  );
}
