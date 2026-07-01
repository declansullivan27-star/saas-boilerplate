import { spawn } from 'node:child_process';
import os from 'node:os';

const CLAUDE_BINARY = 'claude';
const TIMEOUT_MS = 60_000;

type StreamJsonLine
  = | { type: 'stream_event'; event: { type: 'content_block_delta'; delta: { type: 'text_delta'; text: string } } }
    | { type: 'result'; is_error: boolean; result?: string }
    | { type: string };

/**
 * Streams a coach reply by shelling out to the Claude Code CLI in headless mode, authenticated
 * via the machine's Claude subscription (OAuth session from `claude login`) instead of an API key.
 * Tools and MCP servers are disabled so the subprocess only ever produces text.
 */
export function streamCoachReply(options: {
  systemPrompt: string;
  transcript: string;
}): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();

  return new ReadableStream<Uint8Array>({
    start(controller) {
      let child: ReturnType<typeof spawn>;

      try {
        child = spawn(CLAUDE_BINARY, [
          '-p',
          options.transcript,
          '--system-prompt',
          options.systemPrompt,
          '--tools',
          '',
          '--strict-mcp-config',
          '--output-format',
          'stream-json',
          '--include-partial-messages',
          '--verbose',
        ], {
          cwd: os.tmpdir(),
          stdio: ['ignore', 'pipe', 'pipe'],
        });
      } catch {
        controller.enqueue(encoder.encode(coachUnavailableMessage()));
        controller.close();
        return;
      }

      let settled = false;
      let stdoutBuffer = '';
      let stderrTail = '';
      let sawText = false;
      let timer: ReturnType<typeof setTimeout>;

      const finish = (message?: string) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        if (message) {
          controller.enqueue(encoder.encode(message));
        }
        controller.close();
      };

      timer = setTimeout(() => {
        child.kill('SIGKILL');
        finish('\n\n[Coach error: timed out waiting for a response.]');
      }, TIMEOUT_MS);

      child.stdout?.setEncoding('utf8');
      child.stdout?.on('data', (chunk: string) => {
        stdoutBuffer += chunk;
        const lines = stdoutBuffer.split('\n');
        stdoutBuffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.trim()) {
            continue;
          }
          let parsed: StreamJsonLine;
          try {
            parsed = JSON.parse(line);
          } catch {
            continue;
          }

          if (parsed.type === 'stream_event' && 'event' in parsed && parsed.event.type === 'content_block_delta' && parsed.event.delta.type === 'text_delta') {
            sawText = true;
            controller.enqueue(encoder.encode(parsed.event.delta.text));
          }

          if (parsed.type === 'result' && 'is_error' in parsed && parsed.is_error) {
            finish(sawText ? undefined : coachUnavailableMessage(parsed.result));
          }
        }
      });

      child.stderr?.setEncoding('utf8');
      child.stderr?.on('data', (chunk: string) => {
        stderrTail = (stderrTail + chunk).slice(-500);
      });

      child.on('error', (error: NodeJS.ErrnoException) => {
        finish(error.code === 'ENOENT' ? coachUnavailableMessage() : coachUnavailableMessage(error.message));
      });

      child.on('close', (code) => {
        if (code !== 0 && !sawText) {
          finish(coachUnavailableMessage(stderrTail));
        } else {
          finish();
        }
      });
    },
  });
}

function coachUnavailableMessage(detail?: string): string {
  const hint = 'Make sure the `claude` CLI is installed and you are logged in (run `claude login` in a terminal on this machine), then try again.';
  return detail
    ? `\n\n[Coach unavailable: ${detail.trim().slice(0, 300)} — ${hint}]`
    : `\n\n[Coach unavailable: could not reach the Claude Code CLI. ${hint}]`;
}
