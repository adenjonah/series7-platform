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

const ALLOWED_ORIGINS = ["https://adenjonah.github.io", "http://localhost", "http://127.0.0.1"];
const VALID_STATUS = ["done", "review", "in_progress", "reset"];

function corsHeaders(req) {
  const origin = req.headers.get("Origin") || "";
  const allow = ALLOWED_ORIGINS.some((a) => origin.startsWith(a)) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
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
          ).bind(student, item, status, score, note, ts).run();
        }
        return json({ ok: true, ts });
      }

      // --- read one student's progress (student token, or admin) ---
      if (req.method === "GET" && url.pathname === "/progress") {
        const student = url.searchParams.get("student");
        const token = url.searchParams.get("token");
        if (!student) return json({ error: "missing student" }, 400);
        const authed = (tokens[student] && tokens[student] === token) || (env.ADMIN_TOKEN && token === env.ADMIN_TOKEN);
        if (!authed) return json({ error: "bad token" }, 403);
        const { results } = await env.DB
          .prepare("SELECT item, status, score, note, ts FROM progress WHERE student = ? ORDER BY item").bind(student).all();
        return json({ student, progress: results });
      }

      // --- read everyone (coach) ---
      if (req.method === "GET" && url.pathname === "/cohort") {
        if (!env.ADMIN_TOKEN || url.searchParams.get("token") !== env.ADMIN_TOKEN)
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
