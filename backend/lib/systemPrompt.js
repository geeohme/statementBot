/**
 * Assembles the system prompt for the BrightWave chatbot.
 * Combines a set of markdown prompt fragments with live account context
 * (the 6 statements) so the model has everything it needs in a single string.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadStatements } from "./statements.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROMPTS_DIR = path.join(__dirname, "..", "prompts");

const ORDER = [
  "00_identity.md",
  "10_bill_structure.md",
  "20_response_standards.md",
  "30_formatting.md",
  "40_change_explanations.md",
  "50_tools_and_links.md",
  "90_safety_and_limits.md",
];

function readFragment(name) {
  return fs.readFileSync(path.join(PROMPTS_DIR, name), "utf-8");
}

function fragmentText() {
  return ORDER.map(readFragment).join("\n\n---\n\n");
}

/**
 * Build a compact summary of every statement and the full JSON for each.
 * The summary table is what the model uses when the user asks "what
 * statements do I have?" — the full JSON is what it uses for any specific
 * question about numbers.
 */
function statementContext({ list, byId }) {
  const summary = list
    .map(
      (s) =>
        `| ${s.seq} | ${s.billDate} | ${s.servicePeriodStart} → ${s.servicePeriodEnd} | $${s.amountDue} | ${
          s.promoExpirations && s.promoExpirations.length
            ? s.promoExpirations.join("; ")
            : "—"
        } |`,
    )
    .join("\n");

  const full = list
    .map((s) => {
      const data = byId[s.seq];
      return `### Statement ${s.seq} (${s.billDate})\n\`\`\`json\n${JSON.stringify(data, null, 2)}\n\`\`\``;
    })
    .join("\n\n");

  return `
# Account on file

You are speaking on behalf of one specific BrightWave account. **Only answer using the data below.** Never invent line items, dates, amounts, or promotions that aren't shown here.

## Available statements (summary)

| # | Bill date | Service period | Amount due | Notable events |
|---|-----------|----------------|------------|----------------|
${summary}

## Full statement data

${full}
`;
}

export async function buildSystemPrompt() {
  const data = await loadStatements();
  return `${fragmentText()}\n\n---\n\n${statementContext(data)}`;
}
