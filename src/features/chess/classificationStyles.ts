import type { MoveClassification } from '@/features/chess/types';

export const CLASSIFICATION_LABEL: Record<MoveClassification, string> = {
  best: 'Best',
  excellent: 'Excellent',
  good: 'Good',
  inaccuracy: 'Inaccuracy',
  mistake: 'Mistake',
  blunder: 'Blunder',
};

export const CLASSIFICATION_SYMBOL: Record<MoveClassification, string> = {
  best: '★',
  excellent: '✓',
  good: '·',
  inaccuracy: '?!',
  mistake: '?',
  blunder: '??',
};

export const CLASSIFICATION_COLOR: Record<MoveClassification, string> = {
  best: 'text-[var(--matrix-green)]',
  excellent: 'text-[var(--matrix-green-dim)]',
  good: 'text-[oklch(0.75_0.03_150)]',
  inaccuracy: 'text-[var(--matrix-amber)]',
  mistake: 'text-[oklch(0.72_0.19_45)]',
  blunder: 'text-[var(--matrix-red)]',
};
