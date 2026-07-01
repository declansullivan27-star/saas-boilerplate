import type { ChessInsights, GameAnalysisSummary, MoveClassification, SavedGame } from '@/features/chess/types';
import { auth } from '@clerk/nextjs/server';
import { and, asc, eq } from 'drizzle-orm';
import { NextResponse } from 'next/server';
import { addToSummary, emptySummary, mergeSummaries } from '@/features/chess/classify';
import { db } from '@/libs/DB';
import { chessGameSchema, chessMoveSchema } from '@/models/Schema';

const OPENING_PLY_LIMIT = 20;
const MIDDLEGAME_PLY_LIMIT = 60;

export async function GET() {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const games = await db
    .select()
    .from(chessGameSchema)
    .where(eq(chessGameSchema.ownerId, userId));

  if (games.length === 0) {
    const empty: ChessInsights = {
      gamesAnalyzed: 0,
      averageAccuracy: null,
      totals: emptySummary(),
      byPhase: { opening: emptySummary(), middlegame: emptySummary(), endgame: emptySummary() },
      worstGames: [],
    };
    return NextResponse.json(empty satisfies ChessInsights);
  }

  const byPhase = {
    opening: emptySummary(),
    middlegame: emptySummary(),
    endgame: emptySummary(),
  };

  for (const game of games) {
    const moves = await db
      .select()
      .from(chessMoveSchema)
      .where(and(eq(chessMoveSchema.gameId, game.id), eq(chessMoveSchema.color, game.perspective)))
      .orderBy(asc(chessMoveSchema.ply));

    for (const move of moves) {
      const phase = move.ply < OPENING_PLY_LIMIT
        ? 'opening'
        : move.ply < MIDDLEGAME_PLY_LIMIT ? 'middlegame' : 'endgame';
      byPhase[phase] = addToSummary(byPhase[phase], move.classification as MoveClassification);
    }
  }

  const totals: GameAnalysisSummary = mergeSummaries([byPhase.opening, byPhase.middlegame, byPhase.endgame]);

  const accuracies = games.map(game => game.accuracy).filter((value): value is number => value !== null);
  const averageAccuracy = accuracies.length > 0
    ? Math.round((accuracies.reduce((sum, value) => sum + value, 0) / accuracies.length) * 10) / 10
    : null;

  const worstGames: SavedGame[] = [...games]
    .filter(game => game.accuracy !== null)
    .sort((a, b) => (a.accuracy ?? 100) - (b.accuracy ?? 100))
    .slice(0, 5)
    .map(game => ({
      id: game.id,
      lichessId: game.lichessId,
      white: game.white,
      black: game.black,
      result: game.result,
      perspective: game.perspective as 'w' | 'b',
      timeControl: game.timeControl,
      playedAt: game.playedAt?.toISOString() ?? null,
      accuracy: game.accuracy,
      blunders: game.blunders,
      mistakes: game.mistakes,
      inaccuracies: game.inaccuracies,
      createdAt: game.createdAt.toISOString(),
    }));

  const insights: ChessInsights = {
    gamesAnalyzed: games.length,
    averageAccuracy,
    totals,
    byPhase,
    worstGames,
  };

  return NextResponse.json(insights);
}
