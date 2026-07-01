import Anthropic from '@anthropic-ai/sdk';

/** Streams a coach reply via the Anthropic API. Used when ANTHROPIC_API_KEY is configured. */
export function streamCoachReplyViaApi(options: {
  apiKey: string;
  systemPrompt: string;
  messages: { role: 'user' | 'assistant'; content: string }[];
}): ReadableStream<Uint8Array> {
  const anthropic = new Anthropic({ apiKey: options.apiKey });

  const stream = anthropic.messages.stream({
    model: 'claude-sonnet-5',
    max_tokens: 1024,
    system: options.systemPrompt,
    messages: options.messages,
  });

  const encoder = new TextEncoder();

  return new ReadableStream<Uint8Array>({
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
}
