CREATE TABLE "chess_game" (
	"id" serial PRIMARY KEY NOT NULL,
	"owner_id" text NOT NULL,
	"lichess_id" text,
	"pgn" text NOT NULL,
	"white" text NOT NULL,
	"black" text NOT NULL,
	"result" text NOT NULL,
	"perspective" text NOT NULL,
	"time_control" text,
	"played_at" timestamp,
	"accuracy" integer,
	"blunders" integer DEFAULT 0 NOT NULL,
	"mistakes" integer DEFAULT 0 NOT NULL,
	"inaccuracies" integer DEFAULT 0 NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "chess_move" (
	"id" serial PRIMARY KEY NOT NULL,
	"game_id" integer NOT NULL,
	"ply" integer NOT NULL,
	"move_number" integer NOT NULL,
	"color" text NOT NULL,
	"san" text NOT NULL,
	"fen_before" text NOT NULL,
	"fen_after" text NOT NULL,
	"eval_cp_before" integer,
	"eval_cp_after" integer,
	"best_move" text,
	"cp_loss" integer NOT NULL,
	"classification" text NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "chess_move" ADD CONSTRAINT "chess_move_game_id_chess_game_id_fk" FOREIGN KEY ("game_id") REFERENCES "public"."chess_game"("id") ON DELETE cascade ON UPDATE no action;