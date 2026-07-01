'use client';

import type { AnalyzedMove, CoachChatMessage } from '@/features/chess/types';
import { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';

type DisplayMessage = CoachChatMessage & { id: number };

export function CoachChat(props: {
  move: AnalyzedMove | null;
  playerName?: string;
}) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const nextIdRef = useRef(0);

  const ask = async (question: string) => {
    if (!question.trim() || streaming) {
      return;
    }

    const nextMessages: DisplayMessage[] = [
      ...messages,
      { id: nextIdRef.current++, role: 'user', content: question.trim() },
    ];
    setMessages(nextMessages);
    setInput('');
    setError(null);
    setStreaming(true);

    const position = props.move
      ? {
          fen: props.move.fenAfter,
          san: props.move.san,
          moveNumber: props.move.moveNumber,
          color: props.move.color,
          evalCpBefore: props.move.evalBefore.mate !== null ? null : props.move.evalBefore.cp,
          evalCpAfter: props.move.evalAfter.mate !== null ? null : props.move.evalAfter.cp,
          bestMoveSan: props.move.evalBefore.bestMoveSan,
          classification: props.move.classification,
        }
      : {
          fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
          san: null,
          moveNumber: 0,
          color: 'w' as const,
          evalCpBefore: null,
          evalCpAfter: null,
          bestMoveSan: null,
          classification: null,
        };

    try {
      const response = await fetch('/api/chess/coach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages, position, playerName: props.playerName }),
      });

      if (!response.ok || !response.body) {
        const json = await response.json().catch(() => ({}));
        throw new Error(json.error ?? 'The coach could not respond.');
      }

      const assistantId = nextIdRef.current++;
      setMessages(current => [...current, { id: assistantId, role: 'assistant', content: '' }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
        accumulated += decoder.decode(value, { stream: true });
        setMessages(current => [...current.slice(0, -1), { id: assistantId, role: 'assistant', content: accumulated }]);
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'The coach could not respond.');
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="matrix-panel flex h-[420px] flex-col rounded-md p-3">
      <p className="matrix-glow-text mb-2 text-xs tracking-widest uppercase">
        Coach
      </p>

      <div ref={scrollRef} className="flex-1 space-y-2 overflow-y-auto text-sm">
        {messages.length === 0 && (
          <p className="text-xs text-[oklch(0.55_0.03_150)]">
            Ask about the selected move — "why is this a mistake?", "what should I have played?"
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={message.role === 'user'
              ? 'matrix-glow-text'
              : `text-[oklch(0.85_0.02_150)]`}
          >
            <span className="text-[oklch(0.5_0.03_150)]">
              {message.role === 'user' ? '> ' : '$ '}
            </span>
            {message.content || (streaming && index === messages.length - 1 ? '…' : '')}
          </div>
        ))}
        {error && <p className="text-(--matrix-red)">{error}</p>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="mt-2 flex gap-2"
      >
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask the coach…"
          className="
            matrix-glow-border flex-1 rounded-sm border bg-transparent px-2
            py-1.5 text-sm outline-none
          "
        />
        <Button type="submit" size="sm" disabled={streaming}>
          {streaming ? '…' : 'Send'}
        </Button>
      </form>
    </div>
  );
}
