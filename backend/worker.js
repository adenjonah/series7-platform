/**
 * Series 7 progress tracking — Cloudflare Worker over a D1 database.
 *
 * Free-tier fit: D1 free = 100k row-writes/day, 5M reads/day, 5 GB. For 4 students this
 * is ~250x headroom. No inactivity pause (unlike Supabase free).
 *
 * Auth (name-only, by product choice): a student self-identifies by name; reads/writes
 * are open to anyone who names a student on the allowlist (env.STUDENTS). This is a
 * private, low-stakes study tracker — worst case is a friend editing a friend's checkmarks.
 * The COHORT read (all students at once) stays gated behind ADMIN_TOKEN so it isn't
 * trivially public. Input is still validated (item charset, note length) and CORS is an
 * exact-origin allowlist.
 *
 * Endpoints:
 *   POST /progress   {student, item, status, score?, note?}  -> upsert (status "reset" deletes)
 *   GET  /progress?student=X                                 -> that student's rows
 *   GET  /cohort   (header X-Token: ADMIN)                   -> all rows (coach)
 */

const VALID_STATUS = ["done", "review", "in_progress", "reset"];
// item is a module id or a dated event — strict charset, so it can never carry markup.
const ITEM_RE = /^(M\d{1,2}|(?:mock|quiz|daily):\d{4}-\d{2}-\d{2})$/;
const NOTE_MAX = 500;

function students(env) {
  return (env.STUDENTS || "jonah,jojo,adam,sydni").split(",").map((s) => s.trim()).filter(Boolean);
}

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
    const roster = students(env);

    try {
      // --- write a student's progress (name-only) ---
      if (req.method === "POST" && url.pathname === "/progress") {
        const body = await req.json().catch(() => ({}));
        const { student, item, status, score = null, note = null } = body;
        if (!student || !item || !status) return json({ error: "missing student/item/status" }, 400);
        if (!roster.includes(student)) return json({ error: "unknown student" }, 403);
        if (!VALID_STATUS.includes(status)) return json({ error: "bad status" }, 400);
        if (typeof item !== "string" || !ITEM_RE.test(item)) return json({ error: "bad item" }, 400);
        const cleanScore = score == null ? null : (Number.isFinite(+score) ? +score : null);
        const cleanNote = note == null ? null : String(note).slice(0, NOTE_MAX);

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

      // --- read one student's progress (name-only) ---
      if (req.method === "GET" && url.pathname === "/progress") {
        const student = url.searchParams.get("student");
        if (!student) return json({ error: "missing student" }, 400);
        if (!roster.includes(student)) return json({ error: "unknown student" }, 403);
        const { results } = await env.DB
          .prepare("SELECT item, status, score, note, ts FROM progress WHERE student = ? ORDER BY item").bind(student).all();
        return json({ student, progress: results });
      }

      // --- read everyone (coach) — still gated ---
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
