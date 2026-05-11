/**
 * Loads parsed statement JSON from the PDF renderer service.
 * The PDF renderer owns the canonical XML; the backend only consumes
 * pre-parsed JSON via the renderer's /statements/<seq>/json endpoint.
 */

const RENDERER_URL = process.env.RENDERER_URL || "http://localhost:8001";

let cache = null;        // { list: [...], byId: {...}, loadedAt: Date }
const CACHE_TTL_MS = 60_000;

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`Fetch ${url} → ${r.status}`);
  return r.json();
}

export async function loadStatements() {
  if (cache && Date.now() - cache.loadedAt < CACHE_TTL_MS) return cache;

  const list = await fetchJson(`${RENDERER_URL}/statements`);
  const byId = {};
  await Promise.all(
    list.map(async (s) => {
      byId[s.seq] = await fetchJson(`${RENDERER_URL}/statements/${s.seq}/json`);
    }),
  );

  cache = { list, byId, loadedAt: Date.now() };
  return cache;
}

export function rendererUrl() {
  return RENDERER_URL;
}
