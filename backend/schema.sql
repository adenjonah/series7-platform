-- Series 7 progress tracking — Cloudflare D1 (SQLite).
-- One row per (student, item). item is a module id (e.g. "M7"), a mock ("mock:2026-09-01"),
-- a daily-10 ("daily:2026-09-01"), or a weekly quiz ("quiz:2026-09-06").
CREATE TABLE IF NOT EXISTS progress (
  student TEXT NOT NULL,              -- slug: jonah | jojo | adam | sydni
  item    TEXT NOT NULL,
  status  TEXT NOT NULL,              -- done | review | in_progress
  score   REAL,                       -- optional: mock/quiz percentage
  note    TEXT,
  ts      TEXT NOT NULL,              -- ISO-8601 last-updated
  PRIMARY KEY (student, item)
);
CREATE INDEX IF NOT EXISTS progress_student ON progress (student);
