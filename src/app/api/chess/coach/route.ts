import Anthropic from '@anthropic-ai/sdk';
import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';
import * as z from 'zod';
import { Env } from '@/libs/Env';

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

export async function POST(request: Request) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  if (!Env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      { error: 'The AI coach is not configured yet. Set ANTHROPIC_API_KEY to enable it.' },
      { status: 503 },
    );
  }

  const json = await request.json().catch(() => null);
  const parsed = bodySchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const { messages, position, playerName } = parsed.data;
  const anthropic = new Anthropic({ apiKey: Env.ANTHROPIC_API_KEY });

  const stream = anthropic.messages.stream({
    model: 'claude-sonnet-5',
    max_tokens: 1024,
    system: buildSystemPrompt(position, playerName),
    messages: messages.map(message => ({ role: message.role, content: message.content })),
  });

  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for await (const event of stream) {
          if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
            controller.enqueue(encoder.encode(event.delta.text));
          }
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'The AI coach ran into an error.';
        controller.enqueue(encoder.encode(`\n\n[Coach error: ${message}]`));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Cache-Control': 'no-cache',
    },
  });
}
