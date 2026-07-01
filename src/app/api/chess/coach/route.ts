import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import * as z from 'zod';
import { streamCoachReplyViaApi } from '@/features/chess/anthropicApi';
import { streamCoachReply } from '@/features/chess/claudeCli';
import { Env } from '@/libs/Env';

export const runtime = 'nodejs';

const bodySchema = z.object({
  messages: z.array(z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string(),
  })).min(1).max(40),
  position: z.object({
    fen: z.string(),
    san: z.string().nullable(),
    moveNumber: z.number(),
    color: z.enum(['w', 'b']),
    evalCpBefore: z.number().nullable(),
    evalCpAfter: z.number().nullable(),
    bestMoveSan: z.string().nullable(),
    classification: z.string().nullable(),
  }),
  playerName: z.string().optional(),
});

function formatEval(cp: number | null): string {
  if (cp === null) {
    return 'unknown';
  }
  const pawns = (cp / 100).toFixed(2);
  return `${cp >= 0 ? '+' : ''}${pawns} (White's perspective)`;
}

function buildSystemPrompt(position: z.infer<typeof bodySchema>['position'], playerName?: string) {
  return `You are a calm, sharp chess coach inside "Chess Guide Buddy". You are looking at one specific position from a real game, together with real Stockfish engine output. You must never invent an evaluation, a line, or a tactic that isn't backed by the data given to you below — if you're unsure, say so and stick to what the engine numbers actually show.

Position under discussion:
- FEN: ${position.fen}
- Move played: ${position.san ?? 'starting position'} (move ${position.moveNumber}, ${position.color === 'w' ? 'White' : 'Black'} to move before this move)
- Evaluation before the move: ${formatEval(position.evalCpBefore)}
- Evaluation after the move: ${formatEval(position.evalCpAfter)}
- Engine's preferred move here: ${position.bestMoveSan ?? 'not available'}
- Move classification: ${position.classification ?? 'not classified'}
${playerName ? `- The player asking questions is playing as: ${playerName}` : ''}

Style: talk like a strong human coach, not a textbook. Be concrete and specific to this position. Keep answers focused — a few short paragraphs at most unless asked to go deeper. When relevant, reference the actual centipawn swing and the engine's suggested move rather than vague praise or criticism.`;
}

function buildTranscript(messages: z.infer<typeof bodySchema>['messages']): string {
  const transcript = messages
    .map(message => `${message.role === 'user' ? 'User' : 'Coach'}: ${message.content}`)
    .join('\n\n');
  return `${transcript}\n\nRespond only to the latest User message above — don't re-answer earlier turns.`;
}

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

  const { messages, position, playerName } = parsed.data;
  const systemPrompt = buildSystemPrompt(position, playerName);

  // Cloud/CI deployments set ANTHROPIC_API_KEY (pennies per question, works anywhere).
  // Without one — e.g. local dev — fall back to the free Claude Code CLI subscription.
  const body = Env.ANTHROPIC_API_KEY
    ? streamCoachReplyViaApi({ apiKey: Env.ANTHROPIC_API_KEY, systemPrompt, messages })
    : streamCoachReply({ systemPrompt, transcript: buildTranscript(messages) });

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}
