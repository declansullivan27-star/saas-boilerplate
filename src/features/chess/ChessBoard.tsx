'use client';

import { cn } from '@/utils/Helpers';

const PIECE_GLYPHS: Record<string, string> = {
  p: '♟',
  n: '♞',
  b: '♝',
  r: '♜',
  q: '♛',
  k: '♚',
  P: '♙',
  N: '♘',
  B: '♗',
  R: '♖',
  Q: '♕',
  K: '♔',
};

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

function parseBoard(fen: string): (string | null)[][] {
  const boardPart = fen.split(' ')[0] ?? '';
  return boardPart.split('/').map((rank) => {
    const squares: (string | null)[] = [];
    for (const char of rank) {
      if (/\d/.test(char)) {
        squares.push(...Array.from<string | null>({ length: Number(char) }).fill(null));
      } else {
        squares.push(char);
      }
    }
    return squares;
  });
}

export type ChessBoardHighlight = {
  square: string;
  variant: 'lastMoveFrom' | 'lastMoveTo' | 'bestMoveFrom' | 'bestMoveTo';
};

export function ChessBoard(props: {
  fen: string;
  perspective?: 'w' | 'b';
  highlights?: ChessBoardHighlight[];
}) {
  const perspective = props.perspective ?? 'w';
  const rows = parseBoard(props.fen);
  const highlightBySquare = new Map((props.highlights ?? []).map(h => [h.square, h.variant]));

  const ranks = perspective === 'w' ? [8, 7, 6, 5, 4, 3, 2, 1] : [1, 2, 3, 4, 5, 6, 7, 8];
  const files = perspective === 'w' ? FILES : [...FILES].reverse();

  return (
    <div
      className="
        matrix-glow-border grid aspect-square w-full max-w-[560px] grid-cols-8
        overflow-hidden rounded-md border-2
      "
    >
      {ranks.map(rank =>
        files.map((file) => {
          const fileIndex = FILES.indexOf(file);
          const rankIndex = 8 - rank;
          const piece = rows[rankIndex]?.[fileIndex] ?? null;
          const square = `${file}${rank}`;
          const isLight = (fileIndex + rankIndex) % 2 === 0;
          const highlight = highlightBySquare.get(square);

          return (
            <div
              key={square}
              className={cn(
                `
                  relative flex items-center justify-center text-3xl
                  sm:text-4xl
                `,
                isLight
                  ? 'bg-[oklch(0.2_0.02_150)]'
                  : `bg-[oklch(0.13_0.015_150)]`,
                highlight === 'lastMoveFrom' && 'bg-[oklch(0.3_0.1_149/0.9)]',
                highlight === 'lastMoveTo' && 'bg-[oklch(0.38_0.15_149/0.9)]',
                highlight === 'bestMoveFrom' && `
                  ring-2 ring-(--matrix-amber) ring-inset
                `,
                highlight === 'bestMoveTo' && `
                  ring-2 ring-(--matrix-amber) ring-inset
                `,
              )}
            >
              {piece && (
                <span
                  className={cn(
                    piece === piece.toUpperCase()
                      ? 'matrix-glow-text'
                      : `text-[oklch(0.6_0.03_150)]`,
                  )}
                >
                  {PIECE_GLYPHS[piece]}
                </span>
              )}
            </div>
          );
        }),
      )}
    </div>
  );
}
