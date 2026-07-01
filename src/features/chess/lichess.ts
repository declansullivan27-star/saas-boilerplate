import type { LichessGameSummary } from '@/features/chess/types';

const GAME_SEPARATOR = /\n{3,}/;

function extractHeader(pgn: string, tag: string): string | null {
  const match = pgn.match(new RegExp(`\\[${tag} "(.*)"\\]`));
  return match ? match[1]! : null;
}

/**
 * Fetches a user's recent games from the public Lichess API as raw PGN and splits them into
 * individually parseable game records. No API key is required for public game history.
 */
export async function fetchLichessGames(username: string, max = 20): Promise<LichessGameSummary[]> {
  const url = new URL(`https://lichess.org/api/games/user/${encodeURIComponent(username)}`);
  url.searchParams.set('max', String(max));
  url.searchParams.set('clocks', 'false');
  url.searchParams.set('evals', 'false');
  url.searchParams.set('opening', 'false');

  const response = await fetch(url, {
    headers: { Accept: 'application/x-chess-pgn' },
  });

  if (response.status === 404) {
    throw new Error(`No Lichess account found for "${username}"`);
  }
  if (!response.ok) {
    throw new Error(`Lichess API request failed with status ${response.status}`);
  }

  const body = await response.text();
  const rawGames = body.split(GAME_SEPARATOR).map(game => game.trim()).filter(Boolean);

  return rawGames.map((pgn) => {
    const lichessId = extractHeader(pgn, 'Site')?.split('/').pop() ?? crypto.randomUUID();

    return {
      lichessId,
      pgn,
      white: extractHeader(pgn, 'White') ?? 'Unknown',
      black: extractHeader(pgn, 'Black') ?? 'Unknown',
      result: extractHeader(pgn, 'Result') ?? '*',
      timeControl: extractHeader(pgn, 'TimeControl'),
      playedAt: extractHeader(pgn, 'UTCDate') && extractHeader(pgn, 'UTCTime')
        ? `${extractHeader(pgn, 'UTCDate')}T${extractHeader(pgn, 'UTCTime')}Z`
        : null,
      url: `https://lichess.org/${lichessId}`,
    };
  });
}
