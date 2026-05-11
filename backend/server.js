/**
 * BrightWave chatbot backend
 * =========================
 * Express server that wraps Anthropic's Messages API for a multi-turn chat,
 * and proxies statement metadata + PDF rendering from the Python renderer.
 */

import express from "express";
import cors from "cors";
import Anthropic from "@anthropic-ai/sdk";

import { buildSystemPrompt } from "./lib/systemPrompt.js";
import { loadStatements, rendererUrl } from "./lib/statements.js";

const PORT = parseInt(process.env.PORT || "8000", 10);
const MODEL = process.env.ANTHROPIC_MODEL || "claude-haiku-4-5";
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const MAX_TOKENS = parseInt(process.env.MAX_TOKENS || "2048", 10);

if (!ANTHROPIC_API_KEY) {
  console.warn("⚠️  ANTHROPIC_API_KEY not set — /api/chat will fail until it is.");
}

const anthropic = new Anthropic({ apiKey: ANTHROPIC_API_KEY });

const app = express();
app.use(cors());
app.use(express.json({ limit: "1mb" }));


// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

app.get("/api/health", async (_req, res) => {
  try {
    const data = await loadStatements();
    res.json({
      status: "ok",
      model: MODEL,
      statements: data.list.length,
      renderer: rendererUrl(),
    });
  } catch (err) {
    res.status(500).json({ status: "error", message: err.message });
  }
});


// ---------------------------------------------------------------------------
// Statement metadata + proxy routes
// ---------------------------------------------------------------------------

app.get("/api/statements", async (_req, res) => {
  try {
    const { list } = await loadStatements();
    res.json(list);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/statements/:seq/pdf", async (req, res) => {
  const seq = parseInt(req.params.seq, 10);
  try {
    const r = await fetch(`${rendererUrl()}/statements/${seq}/pdf`);
    if (!r.ok) return res.status(r.status).end();
    res.setHeader("Content-Type", "application/pdf");
    res.setHeader(
      "Content-Disposition",
      `inline; filename="brightwave_statement_${seq}.pdf"`,
    );
    const buf = Buffer.from(await r.arrayBuffer());
    res.send(buf);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});

app.get("/api/statements/:seq/xml", async (req, res) => {
  const seq = parseInt(req.params.seq, 10);
  try {
    const r = await fetch(`${rendererUrl()}/statements/${seq}`);
    if (!r.ok) return res.status(r.status).end();
    res.setHeader("Content-Type", "application/xml");
    res.send(await r.text());
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
});


// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------

/**
 * POST /api/chat
 *  body: { messages: [{role:"user"|"assistant", content:"..."} ...] }
 *  returns: { role:"assistant", content:"...", usage:{...} }
 *
 * Multi-turn: the client sends the full conversation each request.
 * The system prompt (identity + bill rules + account data) is rebuilt
 * each call, so any newly generated statements get picked up.
 */
app.post("/api/chat", async (req, res) => {
  const { messages } = req.body || {};
  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: "messages array required" });
  }

  // Coerce / validate roles
  const sanitized = messages
    .filter((m) => m && (m.role === "user" || m.role === "assistant"))
    .map((m) => ({ role: m.role, content: String(m.content || "") }));

  if (sanitized.length === 0) {
    return res.status(400).json({ error: "no valid messages" });
  }

  try {
    const system = await buildSystemPrompt();

    const response = await anthropic.messages.create({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      system,
      messages: sanitized,
    });

    const text = response.content
      .filter((b) => b.type === "text")
      .map((b) => b.text)
      .join("");

    res.json({
      role: "assistant",
      content: text,
      usage: response.usage,
      model: response.model,
    });
  } catch (err) {
    console.error("Chat error:", err);
    res.status(500).json({
      error: err.message || "internal_error",
      status: err.status || null,
    });
  }
});


// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`BrightWave backend listening on :${PORT}`);
  console.log(`  Model: ${MODEL}`);
  console.log(`  Renderer: ${rendererUrl()}`);
});
