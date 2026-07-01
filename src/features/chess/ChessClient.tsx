'use client';

import type { ChessBoardHighlight } from '@/features/chess/ChessBoard';
import type { SelectedGame } from '@/features/chess/GameImportForm';
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChessBoard } from '@/features/chess/ChessBoard';
import { CLASSIFICATION_COLOR, CLASSIFICATION_LABEL } from '@/features/chess/classificationStyles';
import { CoachChat } from '@/features/chess/CoachChat';
import { EvalBar } from '@/features/chess/EvalBar';
import { GameImportForm } from '@/features/chess/GameImportForm';
import { InsightsPanel } from '@/features/chess/InsightsPanel';
import { MatrixRain } from '@/features/chess/MatrixRain';
import { MoveList } from '@/features/chess/MoveList';
import { useGameReview } from '@/features/chess/useGameReview';

export function ChessClient() {
  const [selectedGame, setSelectedGame] = useState<SelectedGame | null>(null);
  const [currentPly, setCurrentPly] = useState(0);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [insightsRefreshKey, setInsightsRefreshKey] = useState(0);

  const { status, progress, analysis, error, run } = useGameReview(
    selectedGame?.pgn ?? null,
    selectedGame?.perspective ?? 'w',
  );

  const currentMove = analysis?.moves[currentPly] ?? null;
  const boardFen = currentMove ? currentMove.fenAfter : 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

  const highlights = useMemo<ChessBoardHighlight[]>(() => {
    if (!currentMove) {
      return [];
    }
    const marks: ChessBoardHighlight[] = [
      { square: currentMove.uci.slice(0, 2), variant: 'lastMoveFrom' },
      { square: currentMove.uci.slice(2, 4), variant: 'lastMoveTo' },
    ];
    const bestUci = currentMove.evalBefore.bestMoveUci;
    if (bestUci && currentMove.classification !== 'best' && currentMove.classification !== 'excellent') {
      marks.push({ square: bestUci.slice(0, 2), variant: 'bestMoveFrom' });
      marks.push({ square: bestUci.slice(2, 4), variant: 'bestMoveTo' });
    }
    return marks;
  }, [currentMove]);

  const startAnalysis = (game: SelectedGame) => {
    setSelectedGame(game);
    setCurrentPly(0);
    setSaveState('idle');
  };

  const saveGame = async () => {
    if (!analysis || !selectedGame) {
      return;
    }
    setSaveState('saving');
    try {
      const response = await fetch('/api/chess/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lichessId: selectedGame.lichessId,
          pgn: analysis.pgn,
          white: analysis.white,
          black: analysis.black,
          result: analysis.result,
          perspective: analysis.perspective,
          timeControl: selectedGame.timeControl,
          playedAt: selectedGame.playedAt,
          accuracy: analysis.accuracy,
          summary: analysis.summary,
          moves: analysis.moves.map(move => ({
            ply: move.ply,
            moveNumber: move.moveNumber,
            color: move.color,
            san: move.san,
            fenBefore: move.fenBefore,
            fenAfter: move.fenAfter,
            evalCpBefore: move.evalBefore.mate !== null ? null : move.evalBefore.cp,
            evalCpAfter: move.evalAfter.mate !== null ? null : move.evalAfter.cp,
            bestMove: move.evalBefore.bestMoveSan,
            cpLoss: move.cpLoss,
            classification: move.classification,
          })),
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to save');
      }
      setSaveState('saved');
      setInsightsRefreshKey(key => key + 1);
    } catch {
      setSaveState('error');
    }
  };

  return (
    <div className="
      chess-matrix dark relative -m-3 min-h-[calc(100vh-72px)] overflow-hidden
      rounded-lg p-3
      sm:p-6
    "
    >
      <MatrixRain />

      <div className="relative z-10 flex flex-col gap-6">
        <div>
          <h1 className="
            matrix-glow-text matrix-flicker text-2xl font-bold tracking-wide
          "
          >
            CHESS_GUIDE_BUDDY.exe
          </h1>
          <p className="text-sm text-[oklch(0.6_0.03_150)]">
            Load a game, let Stockfish walk the board, ask the coach what it means.
          </p>
        </div>

        {!selectedGame && <GameImportForm onGameSelected={startAnalysis} />}

        {selectedGame && (
          <div className="
            flex flex-col gap-6
            lg:flex-row
          "
          >
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between text-sm">
                <p>
                  {selectedGame.white}
                  {' '}
                  vs
                  {' '}
                  {selectedGame.black}
                  {' '}
                  ·
                  {selectedGame.result}
                </p>
                <Button type="button" variant="outline" size="sm" onClick={() => setSelectedGame(null)}>
                  Load another game
                </Button>
              </div>

              {status === 'idle' && (
                <Button type="button" onClick={run}>
                  Run Stockfish review
                </Button>
              )}

              {status === 'analyzing' && (
                <p className="
                  matrix-pulse matrix-panel rounded-md p-2 text-center text-xs
                "
                >
                  Analyzing position
                  {' '}
                  {progress.current}
                  {' '}
                  /
                  {progress.total}
                  …
                </p>
              )}

              {status === 'error' && (
                <p className="text-xs text-(--matrix-red)">{error}</p>
              )}

              <div className="flex gap-3">
                <EvalBar
                  cp={currentMove ? (currentMove.evalAfter.mate !== null ? null : currentMove.evalAfter.cp) : null}
                  mate={currentMove ? currentMove.evalAfter.mate : null}
                  orientation={selectedGame.perspective}
                />
                <ChessBoard fen={boardFen} perspective={selectedGame.perspective} highlights={highlights} />
              </div>

              {analysis && (
                <div className="flex items-center justify-between gap-2">
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={currentPly <= 0}
                      onClick={() => setCurrentPly(p => Math.max(0, p - 1))}
                    >
                      ← Prev
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={currentPly >= analysis.moves.length - 1}
                      onClick={() => setCurrentPly(p => Math.min(analysis.moves.length - 1, p + 1))}
                    >
                      Next →
                    </Button>
                  </div>

                  <Button type="button" size="sm" onClick={saveGame} disabled={saveState === 'saving'}>
                    {saveState === 'saved' ? 'Saved ✓' : saveState === 'saving' ? 'Saving…' : 'Save to history'}
                  </Button>
                </div>
              )}

              {currentMove && (
                <p className="text-xs">
                  <span className={CLASSIFICATION_COLOR[currentMove.classification]}>
                    {CLASSIFICATION_LABEL[currentMove.classification]}
                  </span>
                  {currentMove.classification !== 'best' && currentMove.evalBefore.bestMoveSan && (
                    <span className="ml-2 text-[oklch(0.6_0.03_150)]">
                      engine preferred
                      {' '}
                      {currentMove.evalBefore.bestMoveSan}
                    </span>
                  )}
                </p>
              )}
            </div>

            <div className="flex flex-1 flex-col gap-4">
              {analysis && (
                <MoveList moves={analysis.moves} currentPly={currentPly} onSelect={setCurrentPly} />
              )}

              <CoachChat
                move={currentMove}
                playerName={selectedGame.perspective === 'w' ? selectedGame.white : selectedGame.black}
              />

              <div className="matrix-panel rounded-md p-3">
                <p className="
                  matrix-glow-text mb-2 text-xs tracking-widest uppercase
                "
                >
                  Your insights
                </p>
                <InsightsPanel refreshKey={insightsRefreshKey} />
              </div>
            </div>
          </div>
        )}

        {!selectedGame && (
          <div className="matrix-panel rounded-md p-3">
            <p className="
              matrix-glow-text mb-2 text-xs tracking-widest uppercase
            "
            >
              Your insights
            </p>
            <InsightsPanel refreshKey={insightsRefreshKey} />
          </div>
        )}
      </div>
    </div>
  );
}
