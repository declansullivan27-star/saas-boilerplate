import { auth } from '@clerk/nextjs/server';
import { desc, eq } from 'drizzle-orm';
import { NextResponse } from 'next/server';
import * as z from 'zod';
import { db } from '@/libs/DB';
import { chessGameSchema, chessMoveSchema } from '@/models/Schema';

const saveGameSchema = z.object({
  lichessId: z.string().nullable().optional(),
  pgn: z.string().min(1),
  white: z.string().min(1),
  black: z.string().min(1),
  result: z.string().min(1),
  perspective: z.enum(['w', 'b']),
  timeControl: z.string().nullable().optional(),
  playedAt: z.string().nullable().optional(),
  accuracy: z.number(),
  summary: z.object({
    best: z.number(),
    excellent: z.number(),
    good: z.number(),
    inaccuracy: z.number(),
    mistake: z.number(),
    blunder: z.number(),
  }),
  moves: z.array(z.object({
    ply: z.number(),
    moveNumber: z.number(),
    color: z.enum(['w', 'b']),
    san: z.string(),
    fenBefore: z.string(),
    fenAfter: z.string(),
    evalCpBefore: z.number().nullable(),
    evalCpAfter: z.number().nullable(),
    bestMove: z.string().nullable(),
    cpLoss: z.number(),
    classification: z.string(),
  })),
});

export async function GET() {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const games = await db
    .select()
    .from(chessGameSchema)
    .where(eq(chessGameSchema.ownerId, userId))
    .orderBy(desc(chessGameSchema.createdAt));

  return NextResponse.json({ games });
}

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = saveGameSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const { moves, summary, ...game } = parsed.data;

  const [savedGame] = await db
    .insert(chessGameSchema)
    .values({
      ownerId: userId,
      lichessId: game.lichessId ?? null,
      pgn: game.pgn,
      white: game.white,
      black: game.black,
      result: game.result,
      perspective: game.perspective,
      timeControl: game.timeControl ?? null,
      playedAt: game.playedAt ? new Date(game.playedAt) : null,
      accuracy: Math.round(game.accuracy),
      blunders: summary.blunder,
      mistakes: summary.mistake,
      inaccuracies: summary.inaccuracy,
    })
    .returning();

  if (!savedGame) {
    return NextResponse.json({ error: 'Failed to save game' }, { status: 500 });
  }

  if (moves.length > 0) {
    await db.insert(chessMoveSchema).values(moves.map(move => ({
      gameId: savedGame.id,
      ply: move.ply,
      moveNumber: move.moveNumber,
      color: move.color,
      san: move.san,
      fenBefore: move.fenBefore,
      fenAfter: move.fenAfter,
      evalCpBefore: move.evalCpBefore,
      evalCpAfter: move.evalCpAfter,
      bestMove: move.bestMove,
      cpLoss: Math.round(move.cpLoss),
      classification: move.classification,
    })));
  }

  return NextResponse.json({ game: savedGame }, { status: 201 });
}
