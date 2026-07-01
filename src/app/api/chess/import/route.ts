import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import * as z from 'zod';
import { fetchLichessGames } from '@/features/chess/lichess';

const bodySchema = z.object({
  username: z.string().min(1).max(40),
  max: z.number().int().min(1).max(50).default(15),
});

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  try {
    const games = await fetchLichessGames(parsed.data.username, parsed.data.max);
    return NextResponse.json({ games });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to import games from Lichess';
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
