import type { EngineEval } from '@/features/chess/types';

const ENGINE_SCRIPT_URL = '/stockfish/stockfish-18-lite-single.js';

type PendingEvaluation = {
  resolve: (result: EngineEval) => void;
  bestCp: number | null;
  bestMate: number | null;
  bestDepth: number;
  bestMoveUci: string | null;
};

/**
 * Thin UCI wrapper around the Stockfish WASM build, running in a Web Worker.
 * Client-side only: `new StockfishEngine()` must be called from a browser context.
 */
export class StockfishEngine {
  private worker: Worker;
  private ready: Promise<void>;
  private pending: PendingEvaluation | null = null;

  constructor() {
    this.worker = new Worker(ENGINE_SCRIPT_URL);
    this.ready = this.handshake();
  }

  private handshake(): Promise<void> {
    return new Promise((resolve) => {
      const onMessage = (event: MessageEvent<string>) => {
        if (event.data === 'uciok') {
          this.worker.postMessage('isready');
        }
        if (event.data === 'readyok') {
          this.worker.removeEventListener('message', onMessage);
          resolve();
        }
      };
      this.worker.addEventListener('message', onMessage);
      this.worker.postMessage('uci');
    });
  }

  async waitUntilReady(): Promise<void> {
    await this.ready;
  }

  /** Evaluates a single FEN position and resolves once the search reaches `depth`. */
  async evaluate(fen: string, depth = 14): Promise<EngineEval> {
    await this.ready;

    return new Promise<EngineEval>((resolve) => {
      this.pending = {
        resolve,
        bestCp: null,
        bestMate: null,
        bestDepth: 0,
        bestMoveUci: null,
      };

      const onMessage = (event: MessageEvent<string>) => {
        const line = event.data;

        if (line.startsWith('info') && line.includes('score')) {
          const depthMatch = line.match(/depth (\d+)/);
          const cpMatch = line.match(/score cp (-?\d+)/);
          const mateMatch = line.match(/score mate (-?\d+)/);

          if (depthMatch && this.pending) {
            const reportedDepth = Number(depthMatch[1]);
            if (reportedDepth >= this.pending.bestDepth) {
              this.pending.bestDepth = reportedDepth;
              this.pending.bestCp = cpMatch ? Number(cpMatch[1]) : null;
              this.pending.bestMate = mateMatch ? Number(mateMatch[1]) : null;
            }
          }
        }

        if (line.startsWith('bestmove') && this.pending) {
          const bestMoveMatch = line.match(/bestmove (\S+)/);
          this.pending.bestMoveUci = bestMoveMatch ? bestMoveMatch[1]! : null;

          this.worker.removeEventListener('message', onMessage);
          const result = this.pending;
          this.pending = null;

          resolve({
            cp: result.bestCp,
            mate: result.bestMate,
            bestMoveUci: result.bestMoveUci,
            bestMoveSan: null,
            depth: result.bestDepth,
          });
        }
      };

      this.worker.addEventListener('message', onMessage);
      this.worker.postMessage(`position fen ${fen}`);
      this.worker.postMessage(`go depth ${depth}`);
    });
  }

  terminate(): void {
    this.worker.postMessage('quit');
    this.worker.terminate();
  }
}
