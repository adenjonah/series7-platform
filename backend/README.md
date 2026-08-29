# Progress backend — Cloudflare Worker + D1

Free, no inactivity pause, durable. Stores each student's module/mock progress so
`progress.html` (student) and `coach.html` (cohort) work across devices.

- **Free-tier headroom:** D1 free = 100k row-writes/day, 5M reads/day, 5 GB. Four
  students generate a few hundred writes/day at most — ~250× headroom. Workers free =
  100k requests/day. No project pause (the Supabase-free gotcha).
- **Auth:** a per-student token + one admin token, all Worker **secrets** (never in git).
  A student can only write their own rows; the admin token reads the whole cohort.
- **Files:** `worker.js` (API), `schema.sql` (one `progress` table), `wrangler.toml`
  (config), `package.json` (scripts). `.dev.vars` and `.wrangler/` are gitignored.

## Deploy (one-time)

Run from this `backend/` directory. **Step 2 is the only interactive step** (opens a
browser to log into Cloudflare).

```bash
cd backend
npm install                                   # 1. local wrangler

npx wrangler login                            # 2. INTERACTIVE — browser OAuth to Cloudflare

npx wrangler d1 create series7-progress       # 3. prints a database_id — paste it into wrangler.toml
npx wrangler d1 execute series7-progress --remote --file=schema.sql   # 4. create the table

# 5. generate tokens (one per student + one admin)
for s in jonah jojo adam sydni admin; do echo "$s: $(openssl rand -hex 16)"; done

npx wrangler secret put TOKENS                # 6. paste: {"jonah":"..","jojo":"..","adam":"..","sydni":".."}
npx wrangler secret put ADMIN_TOKEN           #    paste the admin token

npx wrangler deploy                           # 7. prints https://series7-progress.<you>.workers.dev
```

## Hand out the links

Using the Worker URL from step 7 (call it `API`):

- **Each student:**
  `https://adenjonah.github.io/series7-platform/progress.html?api=API&s=<slug>&t=<their-token>`
- **You (coach):**
  `https://adenjonah.github.io/series7-platform/coach.html?api=API&t=<admin-token>`

The `?api=` value sticks in the browser after first visit. Keep these links private —
the token is the only thing gating access.

## Local development (no Cloudflare account needed)

```bash
npm run init-db-local     # apply schema to a local D1
npm run dev               # wrangler dev on http://localhost:8787 (reads .dev.vars)
```

`.dev.vars` (gitignored) holds local test tokens. Point a local `progress.html` at it with
`?api=http://localhost:8787&s=jojo&t=<local-token>`.

## API

| Method | Path | Body / query | Auth |
|---|---|---|---|
| POST | `/progress` | `{student, token, item, status, score?, note?}` — `status` ∈ done/review/in_progress/reset | student token |
| GET | `/progress` | `?student=&token=` | student or admin |
| GET | `/cohort` | `?token=` | admin |

`item` is a module id (`M7`), a mock (`mock:2026-09-01`), a quiz (`quiz:...`), or a daily
(`daily:...`). Writes upsert on `(student, item)`; `status:"reset"` deletes the row.

Verified end-to-end locally 2026-08-28 (miniflare D1): upsert, per-student 403 on wrong
token, admin-gated cohort read, reset/delete, and both HTML pages rendering the round-trip.
