import { integer, pgTable, serial, text, timestamp } from 'drizzle-orm/pg-core';

// This file defines the structure of your database tables using the Drizzle ORM.

// To modify the database schema:
// 1. Update this file with your desired changes.
// 2. Generate a new migration by running: `npm run db:generate`

// The generated migration file will reflect your schema changes.
// It automatically run the command `db-server:file`, which apply the migration before Next.js starts in development mode,
// Alternatively, if your database is running, you can run `npm run db:migrate` and there is no need to restart the server.

// Need a database for production? Check out https://get.neon.com/BMFYNtx
// Tested and compatible with SaaS Boilerplate

export const todoSchema = pgTable('todo', {
  id: serial('id').primaryKey(),
  ownerId: text('owner_id').notNull(),
  title: text('title').notNull(),
  message: text('message').notNull(),
  updatedAt: timestamp('updated_at', { mode: 'date' })
    .defaultNow()
    .$onUpdate(() => new Date())
    .notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).defaultNow().notNull(),
});

export const chessGameSchema = pgTable('chess_game', {
  id: serial('id').primaryKey(),
  ownerId: text('owner_id').notNull(),
  lichessId: text('lichess_id'),
  pgn: text('pgn').notNull(),
  white: text('white').notNull(),
  black: text('black').notNull(),
  result: text('result').notNull(),
  perspective: text('perspective').notNull(), // 'w' | 'b'
  timeControl: text('time_control'),
  playedAt: timestamp('played_at', { mode: 'date' }),
  accuracy: integer('accuracy'),
  blunders: integer('blunders').default(0).notNull(),
  mistakes: integer('mistakes').default(0).notNull(),
  inaccuracies: integer('inaccuracies').default(0).notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).defaultNow().notNull(),
});

export const chessMoveSchema = pgTable('chess_move', {
  id: serial('id').primaryKey(),
  gameId: integer('game_id').notNull().references(() => chessGameSchema.id, { onDelete: 'cascade' }),
  ply: integer('ply').notNull(),
  moveNumber: integer('move_number').notNull(),
  color: text('color').notNull(), // 'w' | 'b'
  san: text('san').notNull(),
  fenBefore: text('fen_before').notNull(),
  fenAfter: text('fen_after').notNull(),
  evalCpBefore: integer('eval_cp_before'),
  evalCpAfter: integer('eval_cp_after'),
  bestMove: text('best_move'),
  cpLoss: integer('cp_loss').notNull(),
  classification: text('classification').notNull(),
  createdAt: timestamp('created_at', { mode: 'date' }).defaultNow().notNull(),
});
