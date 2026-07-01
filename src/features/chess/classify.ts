import type { EngineEval, GameAnalysisSummary, MoveClassification } from '@/features/chess/types';

/** Converts an engine eval to a single centipawn number, from White's perspective, for comparisons. */
export function evalToCp(evaluation: EngineEval): number {
  if (evaluation.mate !== null) {
    const sign = evaluation.mate > 0 ? 1 : -1;
    return sign * (100_000 - Math.abs(evaluation.mate) * 100);
  }

  return evaluation.cp ?? 0;
}

/**
 * Classifies a move from the centipawn loss suffered by the side that played it.
 * Thresholds follow the conventions used by most engine-based review tools.
 */
export function classifyMove(cpLoss: number): MoveClassification {
  if (cpLoss <= 10) {
    return 'best';
  }
  if (cpLoss <= 25) {
    return 'excellent';
  }
  if (cpLoss <= 50) {
    return 'good';
  }
  if (cpLoss <= 100) {
    return 'inaccuracy';
  }
  if (cpLoss <= 200) {
    return 'mistake';
  }
  return 'blunder';
}

/**
 * Win-probability style accuracy estimate for a single move, shaped after Lichess's accuracy curve:
 * a centipawn loss is first converted to a drop in win percentage, then mapped onto a 0-100 accuracy score.
 */
function moveAccuracy(cpLossForMover: number): number {
  const winPercentDrop = 50 * Math.tanh(0.00184104 * Math.max(0, cpLossForMover));
  const accuracy = 103.1668 * Math.exp(-0.04354 * winPercentDrop) - 3.1669;
  return Math.min(100, Math.max(0, accuracy));
}

export function gameAccuracy(cpLosses: number[]): number {
  if (cpLosses.length === 0) {
    return 100;
  }

  const total = cpLosses.reduce((sum, cpLoss) => sum + moveAccuracy(cpLoss), 0);
  return Math.round((total / cpLosses.length) * 10) / 10;
}

export function emptySummary(): GameAnalysisSummary {
  return {
    best: 0,
    excellent: 0,
    good: 0,
    inaccuracy: 0,
    mistake: 0,
    blunder: 0,
  };
}

export function addToSummary(summary: GameAnalysisSummary, classification: MoveClassification): GameAnalysisSummary {
  return {
    ...summary,
    [classification]: summary[classification] + 1,
  };
}

export function mergeSummaries(summaries: GameAnalysisSummary[]): GameAnalysisSummary {
  return summaries.reduce((acc, summary) => ({
    best: acc.best + summary.best,
    excellent: acc.excellent + summary.excellent,
    good: acc.good + summary.good,
    inaccuracy: acc.inaccuracy + summary.inaccuracy,
    mistake: acc.mistake + summary.mistake,
    blunder: acc.blunder + summary.blunder,
  }), emptySummary());
}
