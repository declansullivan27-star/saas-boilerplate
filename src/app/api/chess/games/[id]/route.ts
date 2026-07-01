import { auth } from '@clerk/nextjs/server';
import { and, asc, eq } from 'drizzle-orm';
import { NextResponse } from 'next/server';
import { db } from '@/libs/DB';
import { chessGameSchema, chessMoveSchema } from '@/models/Schema';

type RouteParams = { params: Promise<{ id: string }> };

export async function GET(_request: Request, { params }: RouteParams) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const gameId = Number((await params).id);
  if (!Number.isInteger(gameId)) {
    return NextResponse.json({ error: 'Invalid game id' }, { status: 400 });
  }

  const [game] = await db
    .select()
    .from(chessGameSchema)
    .where(and(eq(chessGameSchema.id, gameId), eq(chessGameSchema.ownerId, userId)));

  if (!game) {
    return NextResponse.json({ error: 'Game not found' }, { status: 404 });
  }

  const moves = await db
    .select()
    .from(chessMoveSchema)
    .where(eq(chessMoveSchema.gameId, gameId))
    .orderBy(asc(chessMoveSchema.ply));

  return NextResponse.json({ game, moves });
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const gameId = Number((await params).id);
  if (!Number.isInteger(gameId)) {
    return NextResponse.json({ error: 'Invalid game id' }, { status: 400 });
  }

  const deleted = await db
    .delete(chessGameSchema)
    .where(and(eq(chessGameSchema.id, gameId), eq(chessGameSchema.ownerId, userId)))
    .returning();

  if (deleted.length === 0) {
    return NextResponse.json({ error: 'Game not found' }, { status: 404 });
  }

  return NextResponse.json({ ok: true });
}
