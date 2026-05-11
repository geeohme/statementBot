/* ============================================================
   BrightWave StatementBot — frontend
   ============================================================ */

const $ = (sel) => document.querySelector(sel);

const els = {
  messages: $("#messages"),
  composer: $("#composer"),
  input: $("#composer-input"),
  sendBtn: $("#send-btn"),
/*  status: $("#health-status"), */
  picker: $("#statement-picker"),
  pdfFrame: $("#pdf-frame"),
  pdfOpen: $("#pdf-open"),
  pdfDownload: $("#pdf-download"),
  suggestions: $("#suggestions"),
};

const state = {
  messages: [],   // {role, content} pairs sent to /api/chat
  statements: [], // list from /api/statements
  sending: false,
};

// ---------- Markdown ----------
marked.setOptions({
  gfm: true,
  breaks: true,
  headerIds: false,
  mangle: false,
});

function renderMarkdown(md) {
  const raw = marked.parse(md || "");
  // Sanitise, but allow target="_blank" on links.
  const cleaned = DOMPurify.sanitize(raw, {
    ADD_ATTR: ["target", "rel"],
  });
  return cleaned;
}

// ---------- Messages ----------

function addMessage(role, content, { stash = true, html = false } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "assistant" || html) {
    bubble.innerHTML = renderMarkdown(content);
    // Force external links to open in a new tab
    bubble.querySelectorAll("a").forEach((a) => {
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener");
    });
  } else {
    bubble.textContent = content;
  }
  wrap.appendChild(bubble);
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  if (stash && role !== "system") {
    state.messages.push({ role, content });
  }
  return wrap;
}

function addThinking() {
  const wrap = document.createElement("div");
  wrap.className = "msg assistant thinking";
  wrap.innerHTML = `<div class="bubble">thinking…</div>`;
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  return wrap;
}

// ---------- Chat ----------

async function sendMessage(text) {
  if (state.sending) return;
  if (!text || !text.trim()) return;

  state.sending = true;
  els.sendBtn.disabled = true;
  addMessage("user", text);
  els.input.value = "";
  autoresize();

  const thinkingEl = addThinking();

  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: state.messages }),
    });

    thinkingEl.remove();

    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      addMessage(
        "system",
        `⚠️ Couldn't reach the assistant (${r.status}). ${err.error || ""}`,
        { stash: false },
      );
      // Don't keep the failed user turn in history
      state.messages.pop();
    } else {
      const body = await r.json();
      addMessage("assistant", body.content || "(empty response)");
    }
  } catch (e) {
    thinkingEl.remove();
    addMessage("system", `⚠️ Network error: ${e.message}`, { stash: false });
    state.messages.pop();
  } finally {
    state.sending = false;
    els.sendBtn.disabled = false;
    els.input.focus();
  }
}

// ---------- Composer ----------

function autoresize() {
  els.input.style.height = "auto";
  els.input.style.height = Math.min(160, els.input.scrollHeight) + "px";
}

els.input.addEventListener("input", autoresize);
els.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage(els.input.value);
  }
});

els.composer.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(els.input.value);
});

// Suggestion chips
els.suggestions.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  sendMessage(btn.dataset.prompt);
});

// ---------- Statements (PDF pane) ----------

function formatStatementLabel(s) {
  const d = new Date(s.billDate);
  const month = d.toLocaleString("en-US", { month: "long", timeZone: "UTC" });
  const year = d.getUTCFullYear();
  const flag = s.promoExpirations && s.promoExpirations.length ? " ⚠️" : "";
  return `${month} ${year} · $${s.amountDue}${flag}`;
}

function selectStatement(seq) {
  const s = state.statements.find((x) => x.seq === seq);
  if (!s) return;
  const url = `/api/statements/${seq}/pdf`;
  els.pdfFrame.src = `${url}#zoom=page-fit`;
  els.pdfOpen.href = url;
  els.pdfDownload.href = url;
  els.pdfDownload.download = `BrightWave_Statement_${s.billDate}.pdf`;
}

async function loadStatements() {
  try {
    const r = await fetch("/api/statements");
    if (!r.ok) throw new Error(`status ${r.status}`);
    const list = await r.json();
    state.statements = list;
    els.picker.innerHTML = "";
    list.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.seq;
      opt.textContent = formatStatementLabel(s);
      els.picker.appendChild(opt);
    });
    // Default to the most recent
    const latest = list[list.length - 1];
    els.picker.value = latest.seq;
    selectStatement(latest.seq);
  } catch (e) {
    console.error("loadStatements failed:", e);
  }
}

els.picker.addEventListener("change", () => {
  selectStatement(parseInt(els.picker.value, 10));
});

// ---------- Health ----------

async function pollHealth() {
  try {
    const r = await fetch("/api/health");
    if (!r.ok) throw new Error();
    const body = await r.json();
    els.status.className = "status ok";
    els.status.innerHTML = `<span class="dot"></span> ${body.statements} statements · ${body.model}`;
  } catch (e) {
    els.status.className = "status err";
    els.status.innerHTML = `<span class="dot"></span> offline`;
  }
}

// ---------- Boot ----------

function greet() {
  const opening = [
    "Hi! I'm Bill, the **BrightWave StatementBot** — your statement assistant.",
    "",
    "I can explain your charges, compare bills month-to-month, walk you through any changes, and pull up your statement PDFs.",
    "",
    "Try one of the suggestions below, or ask anything about your bill.",
  ].join("\n");
  addMessage("assistant", opening, { stash: false });
}

async function init() {
  greet();
  await Promise.all([loadStatements(), pollHealth()]);
  setInterval(pollHealth, 30_000);
}

init();
