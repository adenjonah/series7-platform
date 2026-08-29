/**
 * Series 7 progress tracking — Cloudflare Worker over a D1 database.
 *
 * Free-tier fit: D1 free = 100k row-writes/day, 5M reads/day, 5 GB. For 4 students this
 * is ~250x headroom. No inactivity pause (unlike Supabase free).
 *
 * Auth: per-student token (env.TOKENS = JSON like {"jojo":"..."}), plus an ADMIN_TOKEN
 * for the coach view. Tokens are Worker secrets — never committed. A student may only
 * write their own rows; the coach token can read everything.
 *
 * Endpoints:
 *   POST /progress   {student, token, item, status, score?, note?}  -> upsert (status "reset" deletes)
 *   GET  /progress?student=X&token=Y                                -> that student's rows
 *   GET  /cohort?token=ADMIN                                        -> all rows (coach)
 */

const VALID_STATUS = ["done", "review", "in_progress", "reset"];
// item is a module id or a dated event — strict charset, so it can never carry markup.
const ITEM_RE = /^(M\d{1,2}|(?:mock|quiz|daily):\d{4}-\d{2}-\d{2})$/;
const NOTE_MAX = 500;

// Exact-origin allowlist. Substring/startsWith matching would let
// https://adenjonah.github.io.evil.com or http://localhost.evil.com through.
function allowedOrigin(origin) {
  if (origin === "https://adenjonah.github.io") return origin;
  try {
    const u = new URL(origin);
    if ((u.protocol === "http:" || u.protocol === "https:") && (u.hostname === "localhost" || u.hostname === "127.0.0.1"))
      return origin; // any port, for local dev
  } catch { /* not a URL */ }
  return null;
}

function corsHeaders(req) {
  const allow = allowedOrigin(req.headers.get("Origin") || "");
  const h = { "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type, X-Token", "Vary": "Origin" };
  if (allow) h["Access-Control-Allow-Origin"] = allow; // only reflect a real match; no header => browser blocks
  return h;
}

export default {
  async fetch(req, env) {
    const cors = corsHeaders(req);
    const json = (obj, status = 200) =>
      new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });

    if (req.method === "OPTIONS") return new Response(null, { headers: cors });

    const url = new URL(req.url);
    let tokens = {};
    try { tokens = JSON.parse(env.TOKENS || "{}"); } catch { /* misconfigured secret */ }

    try {
      // --- write a student's progress ---
      if (req.method === "POST" && url.pathname === "/progress") {
        const body = await req.json().catch(() => ({}));
        const { student, token, item, status, score = null, note = null } = body;
        if (!student || !item || !status) return json({ error: "missing student/item/status" }, 400);
        if (!VALID_STATUS.includes(status)) return json({ error: "bad status" }, 400);
        if (typeof item !== "string" || !ITEM_RE.test(item)) return json({ error: "bad item" }, 400);
        const cleanScore = score == null ? null : (Number.isFinite(+score) ? +score : null);
        const cleanNote = note == null ? null : String(note).slice(0, NOTE_MAX);
        if (!tokens[student] || tokens[student] !== token) return json({ error: "bad token" }, 403);

        const ts = new Date().toISOString();
        if (status === "reset") {
          await env.DB.prepare("DELETE FROM progress WHERE student = ? AND item = ?").bind(student, item).run();
        } else {
          await env.DB.prepare(
            `INSERT INTO progress (student, item, status, score, note, ts)
             VALUES (?, ?, ?, ?, ?, ?)
             ON CONFLICT(student, item) DO UPDATE SET
               status = excluded.status, score = excluded.score, note = excluded.note, ts = excluded.ts`
          ).bind(student, item, status, cleanScore, cleanNote, ts).run();
        }
        return json({ ok: true, ts });
      }

      // --- read one student's progress (student token, or admin) ---
      if (req.method === "GET" && url.pathname === "/progress") {
        const student = url.searchParams.get("student");
        const token = req.headers.get("X-Token") || ""; // token in a header, never the URL (keeps it out of request logs)
        if (!student) return json({ error: "missing student" }, 400);
        const authed = (tokens[student] && tokens[student] === token) || (env.ADMIN_TOKEN && token === env.ADMIN_TOKEN);
        if (!authed) return json({ error: "bad token" }, 403);
        const { results } = await env.DB
          .prepare("SELECT item, status, score, note, ts FROM progress WHERE student = ? ORDER BY item").bind(student).all();
        return json({ student, progress: results });
      }

      // --- read everyone (coach) ---
      if (req.method === "GET" && url.pathname === "/cohort") {
        if (!env.ADMIN_TOKEN || req.headers.get("X-Token") !== env.ADMIN_TOKEN)
          return json({ error: "bad token" }, 403);
        const { results } = await env.DB
          .prepare("SELECT student, item, status, score, ts FROM progress ORDER BY student, item").all();
        return json({ progress: results });
      }

      return json({ error: "not found" }, 404);
    } catch (e) {
      return json({ error: String(e && e.message || e) }, 500);
    }
  },
};
