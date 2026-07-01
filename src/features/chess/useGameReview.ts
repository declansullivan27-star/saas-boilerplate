'use client';

import type { AnalyzedMove, EngineEval, GameAnalysis, PieceColor } from '@/features/chess/types';
import { Chess } from 'chess.js';
import { useCallback, useEffect, useRef, useState } from 'react';
import { addToSummary, classifyMove, emptySummary, evalToCp, gameAccuracy } from '@/features/chess/classify';
import { StockfishEngine } from '@/features/chess/stockfishEngine';

export type ReviewStatus = 'idle' | 'analyzing' | 'done' | 'error';

export type ReviewProgress = {
  current: number;
  total: number;
};

/** Normalizes a raw UCI score (from the perspective of the side to move) into White's perspective. */
function toWhitePerspective(rawCp: number | null, rawMate: number | null, sideToMove: PieceColor): { cp: number | null; mate: number | null } {
  const sign = sideToMove === 'w' ? 1 : -1;
  return {
    cp: rawCp === null ? null : sign * rawCp,
    mate: rawMate === null ? null : sign * rawMate,
  };
}

export function useGameReview(pgn: string | null, perspective: PieceColor, depth = 14) {
  const [status, setStatus] = useState<ReviewStatus>('idle');
  const [progress, setProgress] = useState<ReviewProgress>({ current: 0, total: 0 });
  const [analysis, setAnalysis] = useState<GameAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const engineRef = useRef<StockfishEngine | null>(null);
  const cancelledRef = useRef(false);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
      engineRef.current?.terminate();
    };
  }, []);

  const run = useCallback(async () => {
    if (!pgn) {
      return;
    }

    cancelledRef.current = false;
    setStatus('analyzing');
    setError(null);
    setAnalysis(null);

    try {
      const chess = new Chess();
      chess.loadPgn(pgn);
      const headers = chess.getHeaders();
      const verboseMoves = chess.history({ verbose: true });

      chess.reset();
      const fens = [chess.fen()];
      for (const move of verboseMoves) {
        chess.move(move.san);
        fens.push(chess.fen());
      }

      if (!engineRef.current) {
        engineRef.current = new StockfishEngine();
      }
      const engine = engineRef.current;
      await engine.waitUntilReady();

      setProgress({ current: 0, total: fens.length });

      const evaluations: EngineEval[] = [];
      for (let i = 0; i < fens.length; i++) {
        if (cancelledRef.current) {
          return;
        }

        const fen = fens[i]!;
        const sideToMove: PieceColor = fen.split(' ')[1] === 'b' ? 'b' : 'w';
        const raw = await engine.evaluate(fen, depth);
        const normalized = toWhitePerspective(raw.cp, raw.mate, sideToMove);

        evaluations.push({
          cp: normalized.cp,
          mate: normalized.mate,
          bestMoveUci: raw.bestMoveUci,
          bestMoveSan: uciToSan(fen, raw.bestMoveUci),
          depth: raw.depth,
        });

        setProgress({ current: i + 1, total: fens.length });
      }

      const moves: AnalyzedMove[] = [];
      let summary = emptySummary();
      const cpLosses: number[] = [];

      for (let ply = 0; ply < verboseMoves.length; ply++) {
        const move = verboseMoves[ply]!;
        const color: PieceColor = move.color as PieceColor;
        const evalBefore = evaluations[ply]!;
        const evalAfter = evaluations[ply + 1]!;

        const beforeCp = evalToCp(evalBefore);
        const afterCp = evalToCp(evalAfter);
        const rawCpLoss = color === 'w' ? beforeCp - afterCp : afterCp - beforeCp;
        const cpLoss = Math.max(0, Math.min(1000, rawCpLoss));
        const classification = classifyMove(cpLoss);

        if (color === perspective) {
          summary = addToSummary(summary, classification);
          cpLosses.push(cpLoss);
        }

        moves.push({
          ply,
          moveNumber: Math.floor(ply / 2) + 1,
          color,
          san: move.san,
          uci: `${move.from}${move.to}${move.promotion ?? ''}`,
          fenBefore: move.before,
          fenAfter: move.after,
          evalBefore,
          evalAfter,
          cpLoss,
          classification,
        });
      }

      setAnalysis({
        pgn,
        white: headers.White ?? 'White',
        black: headers.Black ?? 'Black',
        result: headers.Result ?? '*',
        perspective,
        moves,
        accuracy: gameAccuracy(cpLosses),
        summary,
      });
      setStatus('done');
    } catch (caughtError) {
      if (!cancelledRef.current) {
        setError(caughtError instanceof Error ? caughtError.message : 'Failed to analyze game');
        setStatus('error');
      }
    }
  }, [pgn, perspective, depth]);

  return { status, progress, analysis, error, run };
}

function uciToSan(fen: string, uci: string | null): string | null {
  if (!uci) {
    return null;
  }

  try {
    const chess = new Chess(fen);
    const move = chess.move({
      from: uci.slice(0, 2),
      to: uci.slice(2, 4),
      promotion: uci.length > 4 ? uci.slice(4) : undefined,
    });
    return move?.san ?? null;
  } catch {
    return null;
  }
}
