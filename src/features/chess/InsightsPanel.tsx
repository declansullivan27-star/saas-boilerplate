'use client';

import type { ChessInsights, GameAnalysisSummary } from '@/features/chess/types';
import { useEffect, useState } from 'react';
import { CLASSIFICATION_COLOR, CLASSIFICATION_LABEL } from '@/features/chess/classificationStyles';

function SummaryBars(props: { summary: GameAnalysisSummary }) {
  const entries = Object.entries(props.summary) as [keyof GameAnalysisSummary, number][];
  const max = Math.max(1, ...entries.map(([, count]) => count));

  return (
    <div className="flex flex-col gap-1">
      {entries.map(([key, count]) => (
        <div
          key={key}
          className="grid grid-cols-[6rem_1fr_2rem] items-center gap-2 text-xs"
        >
          <span className={CLASSIFICATION_COLOR[key]}>{CLASSIFICATION_LABEL[key]}</span>
          <div className="
            h-2 overflow-hidden rounded-sm bg-[oklch(0.2_0.01_150)]
          "
          >
            <div
              className="h-full bg-(--matrix-green)"
              style={{ width: `${(count / max) * 100}%` }}
            />
          </div>
          <span className="text-right text-[oklch(0.6_0.03_150)]">{count}</span>
        </div>
      ))}
    </div>
  );
}

export function InsightsPanel(props: { refreshKey: number }) {
  const [insights, setInsights] = useState<ChessInsights | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetch('/api/chess/insights', { signal: controller.signal })
      .then(res => res.json())
      .then((data: ChessInsights) => setInsights(data))
      .catch(() => {})
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => {
      controller.abort();
    };
  }, [props.refreshKey]);

  if (loading) {
    return <p className="text-xs text-[oklch(0.6_0.03_150)]">Loading insights…</p>;
  }

  if (!insights || insights.gamesAnalyzed === 0) {
    return (
      <p className="text-xs text-[oklch(0.6_0.03_150)]">
        Analyze and save a game to start building your insight history.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4 text-sm">
      <div className="flex gap-6">
        <div>
          <p className="matrix-glow-text text-2xl font-bold">{insights.gamesAnalyzed}</p>
          <p className="text-xs text-[oklch(0.6_0.03_150)]">games analyzed</p>
        </div>
        <div>
          <p className="matrix-glow-text text-2xl font-bold">
            {insights.averageAccuracy ?? '–'}
          </p>
          <p className="text-xs text-[oklch(0.6_0.03_150)]">avg. accuracy</p>
        </div>
      </div>

      <div>
        <p className="
          mb-1 text-xs tracking-widest text-[oklch(0.6_0.03_150)] uppercase
        "
        >
          All moves
        </p>
        <SummaryBars summary={insights.totals} />
      </div>

      <div>
        <p className="
          mb-1 text-xs tracking-widest text-[oklch(0.6_0.03_150)] uppercase
        "
        >
          Blunders by phase
        </p>
        <div className="grid grid-cols-3 gap-2 text-center text-xs">
          <div>
            <p className="text-(--matrix-red)">{insights.byPhase.opening.blunder}</p>
            <p className="text-[oklch(0.6_0.03_150)]">opening</p>
          </div>
          <div>
            <p className="text-(--matrix-red)">{insights.byPhase.middlegame.blunder}</p>
            <p className="text-[oklch(0.6_0.03_150)]">middlegame</p>
          </div>
          <div>
            <p className="text-(--matrix-red)">{insights.byPhase.endgame.blunder}</p>
            <p className="text-[oklch(0.6_0.03_150)]">endgame</p>
          </div>
        </div>
      </div>

      {insights.worstGames.length > 0 && (
        <div>
          <p className="
            mb-1 text-xs tracking-widest text-[oklch(0.6_0.03_150)] uppercase
          "
          >
            Rockiest games
          </p>
          <ul className="flex flex-col gap-1 text-xs">
            {insights.worstGames.map(game => (
              <li key={game.id} className="flex justify-between">
                <span>
                  {game.white}
                  {' '}
                  vs
                  {' '}
                  {game.black}
                </span>
                <span className="text-(--matrix-amber)">
                  {game.accuracy}
                  %
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
