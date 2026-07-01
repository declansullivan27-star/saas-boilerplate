export type MoveClassification
  = | 'best'
    | 'excellent'
    | 'good'
    | 'inaccuracy'
    | 'mistake'
    | 'blunder';

export type PieceColor = 'w' | 'b';

export type EngineEval = {
  /** Centipawns from White's perspective. Null when a forced mate is on the board. */
  cp: number | null;
  /** Moves to mate from White's perspective (positive = White mates, negative = White gets mated). */
  mate: number | null;
  bestMoveUci: string | null;
  bestMoveSan: string | null;
  depth: number;
};

export type AnalyzedMove = {
  ply: number;
  moveNumber: number;
  color: PieceColor;
  san: string;
  uci: string;
  fenBefore: string;
  fenAfter: string;
  evalBefore: EngineEval;
  evalAfter: EngineEval;
  cpLoss: number;
  classification: MoveClassification;
};

export type GameAnalysisSummary = {
  best: number;
  excellent: number;
  good: number;
  inaccuracy: number;
  mistake: number;
  blunder: number;
};

export type GameAnalysis = {
  pgn: string;
  white: string;
  black: string;
  result: string;
  perspective: PieceColor;
  moves: AnalyzedMove[];
  accuracy: number;
  summary: GameAnalysisSummary;
};

export type LichessGameSummary = {
  lichessId: string;
  pgn: string;
  white: string;
  black: string;
  result: string;
  timeControl: string | null;
  playedAt: string | null;
  url: string;
};

export type SavedGame = {
  id: number;
  lichessId: string | null;
  white: string;
  black: string;
  result: string;
  perspective: PieceColor;
  timeControl: string | null;
  playedAt: string | null;
  accuracy: number | null;
  blunders: number;
  mistakes: number;
  inaccuracies: number;
  createdAt: string;
};

export type ChessInsights = {
  gamesAnalyzed: number;
  averageAccuracy: number | null;
  totals: GameAnalysisSummary;
  byPhase: {
    opening: GameAnalysisSummary;
    middlegame: GameAnalysisSummary;
    endgame: GameAnalysisSummary;
  };
  worstGames: SavedGame[];
};

export type CoachChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};
