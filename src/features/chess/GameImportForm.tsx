'use client';

import type { LichessGameSummary, PieceColor } from '@/features/chess/types';
import { useState } from 'react';
import { Button } from '@/components/ui/button';

export type SelectedGame = {
  pgn: string;
  white: string;
  black: string;
  result: string;
  lichessId: string | null;
  timeControl: string | null;
  playedAt: string | null;
  perspective: PieceColor;
};

function guessPerspective(username: string, white: string): PieceColor {
  return white.toLowerCase() === username.toLowerCase() ? 'w' : 'b';
}

export function GameImportForm(props: {
  onGameSelected: (game: SelectedGame) => void;
}) {
  const [username, setUsername] = useState('');
  const [games, setGames] = useState<LichessGameSummary[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pastedPgn, setPastedPgn] = useState('');

  const importFromLichess = async () => {
    if (!username.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    setGames(null);

    try {
      const response = await fetch('/api/chess/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), max: 15 }),
      });
      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.error ?? 'Failed to import games');
      }
      setGames(json.games);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Failed to import games');
    } finally {
      setLoading(false);
    }
  };

  const selectLichessGame = (game: LichessGameSummary) => {
    props.onGameSelected({
      pgn: game.pgn,
      white: game.white,
      black: game.black,
      result: game.result,
      lichessId: game.lichessId,
      timeControl: game.timeControl,
      playedAt: game.playedAt,
      perspective: guessPerspective(username.trim(), game.white),
    });
  };

  const submitPastedPgn = () => {
    if (!pastedPgn.trim()) {
      return;
    }
    const whiteMatch = pastedPgn.match(/\[White "(.*)"\]/);
    const blackMatch = pastedPgn.match(/\[Black "(.*)"\]/);
    const resultMatch = pastedPgn.match(/\[Result "(.*)"\]/);

    props.onGameSelected({
      pgn: pastedPgn.trim(),
      white: whiteMatch?.[1] ?? 'White',
      black: blackMatch?.[1] ?? 'Black',
      result: resultMatch?.[1] ?? '*',
      lichessId: null,
      timeControl: null,
      playedAt: null,
      perspective: 'w',
    });
  };

  return (
    <div className="matrix-panel flex flex-col gap-4 rounded-md p-4">
      <div>
        <p className="matrix-glow-text mb-2 text-xs tracking-widest uppercase">
          Load from Lichess
        </p>
        <div className="flex gap-2">
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && importFromLichess()}
            placeholder="lichess username"
            className="
              matrix-glow-border flex-1 rounded-sm border bg-transparent px-2
              py-1.5 text-sm outline-none
            "
          />
          <Button type="button" onClick={importFromLichess} disabled={loading}>
            {loading ? 'Loading…' : 'Import'}
          </Button>
        </div>
        {error && <p className="mt-2 text-xs text-(--matrix-red)">{error}</p>}
      </div>

      {games && games.length > 0 && (
        <div className="max-h-56 overflow-y-auto text-sm">
          {games.map(game => (
            <button
              key={game.lichessId}
              type="button"
              onClick={() => selectLichessGame(game)}
              className="
                flex w-full items-center justify-between rounded-sm px-2 py-1.5
                text-left
                hover:bg-[oklch(0.25_0.02_150)]
              "
            >
              <span>
                {game.white}
                {' '}
                vs
                {' '}
                {game.black}
              </span>
              <span className="text-[oklch(0.6_0.03_150)]">{game.result}</span>
            </button>
          ))}
        </div>
      )}

      {games && games.length === 0 && (
        <p className="text-xs text-[oklch(0.6_0.03_150)]">No games found for that account.</p>
      )}

      <div>
        <p className="matrix-glow-text mb-2 text-xs tracking-widest uppercase">
          Or paste a PGN
        </p>
        <textarea
          value={pastedPgn}
          onChange={e => setPastedPgn(e.target.value)}
          rows={4}
          placeholder="[Event ...] 1. e4 e5 2. ..."
          className="
            matrix-glow-border w-full rounded-sm border bg-transparent p-2
            font-mono text-xs outline-none
          "
        />
        <Button type="button" variant="outline" className="mt-2" onClick={submitPastedPgn}>
          Analyze pasted game
        </Button>
      </div>
    </div>
  );
}
