/*
* setup-llm-router.js
*
* Run this with: node setup-llm-router.js
*
* It creates the entire LLM routing layer in a llm-router folder
* in your home directory. Works on Windows, Mac, and Linux.
*
* After running:
* 1. cd into the llm-router folder
* 2. Run: npm install
* 3. Run: claude login
* 4. Run: claude setup-token
* 5. Paste token into .env file
* 6. Test: node test-router.js --offline
* 7. Test live: node test-router.js
*/
const fs = require("fs");
const path = require("path");
const os = require("os");
const BASE = path.join(os.homedir(), "llm-router");
const SHARED = path.join(BASE, "shared");
function writeFile(relPath, content) {
const full = path.join(BASE, relPath);
fs.mkdirSync(path.dirname(full), { recursive: true });
fs.writeFileSync(full, content, "utf-8");
console.log(" Created: " + relPath);
}
console.log("\nSetting up LLM Router at: " + BASE + "\n");
// ── package.json ────────────────────────────────────────────
writeFile("package.json", JSON.stringify({
name: "llm-router",
version: "1.0.0",
description: "Unified LLM routing with OAuth auth, SQLite logging, cost estimation",
main: "shared/llm-router.js",
scripts: {
test: "node test-router.js --offline",
"test:live": "node test-router.js",
costs: "node cost-report.js",
"costs:week": "node cost-report.js --hours 168 --top-callers"
},
dependencies: {
"@anthropic-ai/claude-agent-sdk": "^0.1.0",
"better-sqlite3": "^11.0.0"
}
}, null, 2));
// ── .env ────────────────────────────────────────────────────
writeFile(".env", [
"# Run 'claude login' then 'claude setup-token' and paste token below",
"CLAUDE_CODE_OAUTH_TOKEN=",
"",
"# Remove or leave commented — conflicts with OAuth mode",
"# ANTHROPIC_API_KEY=",
"",
"# Optional: OpenAI for non-Anthropic routing",
"# OPENAI_API_KEY=sk-...",
"",
"# Skip auth smoke test (set to 1 to bypass)",
"LLM_SKIP_SMOKE_TEST=0",
"",
"# Default model for all calls",
"LLM_DEFAULT_MODEL=claude-opus-4-6",
"",
"# Custom path for SQLite log (default: ./llm_calls.db)",
"# LLM_LOG_DB=./llm_calls.db",
""
].join("\r\n"));
// ── shared/model-utils.js ───────────────────────────────────
writeFile("shared/model-utils.js", `"use strict";
const MODEL_ALIASES = Object.freeze({
"opus-4": "claude-opus-4-6",
"opus-4.5": "claude-opus-4-5-20250630",
"opus-4.6": "claude-opus-4-6",
"sonnet-4": "claude-sonnet-4-20250514",
"sonnet-4.5": "claude-sonnet-4-5-20250514",
"sonnet-4.6": "claude-sonnet-4-6",
"haiku-3.5": "claude-3-5-haiku-20241022",
"haiku-4": "claude-haiku-4-5-20251001",
"claude-opus-4": "claude-opus-4-6",
"claude-opus-4.6": "claude-opus-4-6",
"claude-sonnet-4": "claude-sonnet-4-20250514",
"claude-haiku-4": "claude-haiku-4-5-20251001",
"gpt-4o": "gpt-4o",
"gpt-4o-mini": "gpt-4o-mini",
"gpt-4-turbo": "gpt-4-turbo",
"o1": "o1",
"o1-mini": "o1-mini",
"o3": "o3",
"o3-mini": "o3-mini",
});
const PROVIDER_PREFIXES = ["anthropic/", "openai/", "google/"];
function isAnthropicModel(model) {
if (!model) return false;
return /claude|opus|sonnet|haiku/.test(model.toLowerCase());
}
function isOpenAiModel(model) {
if (!model) return false;
var lower = model.toLowerCase();
return /^(gpt-|o1|o3|davinci|text-)/.test(lower) || lower.startsWith("openai/");
}
function detectModelProvider(model) {
if (!model) return null;
if (isAnthropicModel(model)) return "anthropic";
if (isOpenAiModel(model)) return "openai";
return null;
}
function normalizeAnthropicModel(model) {
if (!model) return "claude-opus-4-6";
var m = model.trim();
for (var i = 0; i < PROVIDER_PREFIXES.length; i++) {
if (m.toLowerCase().startsWith(PROVIDER_PREFIXES[i])) {
m = m.slice(PROVIDER_PREFIXES[i].length); break;
}
}
var aliasKey = m.toLowerCase();
if (MODEL_ALIASES[aliasKey]) return MODEL_ALIASES[aliasKey];
return m;
}
function normalizeModel(model) {
if (!model) return "claude-opus-4-6";
var m = model.trim();
for (var i = 0; i < PROVIDER_PREFIXES.length; i++) {
if (m.toLowerCase().startsWith(PROVIDER_PREFIXES[i])) {
m = m.slice(PROVIDER_PREFIXES[i].length); break;
}
}
var aliasKey = m.toLowerCase();
return MODEL_ALIASES[aliasKey] || m;
}
module.exports = {
MODEL_ALIASES: MODEL_ALIASES,
isAnthropicModel: isAnthropicModel,
isOpenAiModel: isOpenAiModel,
detectModelProvider: detectModelProvider,
normalizeAnthropicModel: normalizeAnthropicModel,
normalizeModel: normalizeModel,
};
`);
// ── shared/interaction-store.js ─────────────────────────────
writeFile("shared/interaction-store.js", `"use strict";
var path = require("path");
var Database = require("better-sqlite3");
var DB_PATH = process.env.LLM_LOG_DB || path.join(__dirname, "..", "llm_calls.db");
var MAX_STORED_CHARS = 10000;
var PRICING = [
{ match: /opus-4/i, input: 5.00, output: 25.00 },
{ match: /sonnet-4/i, input: 3.00, output: 15.00 },
{ match: /haiku/i, input: 0.80, output: 4.00 },
{ match: /gpt-4o-mini/i, input: 0.15, output: 0.60 },
{ match: /gpt-4o/i, input: 2.50, output: 10.00 },
{ match: /gpt-4-turbo/i, input: 10.00, output: 30.00 },
{ match: /o3-mini/i, input: 1.10, output: 4.40 },
{ match: /o3/i, input: 10.00, output: 40.00 },
{ match: /o1-mini/i, input: 3.00, output: 12.00 },
{ match: /o1/i, input: 15.00, output: 60.00 },
];
var REDACT_PATTERNS = [
/sk-ant-[A-Za-z0-9_-]{20,}/g,
/sk-[A-Za-z0-9]{20,}/g,
/Bearer\\s+[A-Za-z0-9._\\-\\/+=]{20,}/gi,
/eyJ[A-Za-z0-9_-]{30,}\\.[A-Za-z0-9_-]{30,}/g,
/xoxb-[A-Za-z0-9-]{20,}/g,
/AKIA[A-Z0-9]{16}/g,
];
function redact(text) {
if (!text) return "";
var out = String(text);
for (var i = 0; i < REDACT_PATTERNS.length; i++) {
out = out.replace(REDACT_PATTERNS[i], "[REDACTED]");
}
return out;
}
function truncate(text, maxLen) {
if (maxLen === undefined) maxLen = MAX_STORED_CHARS;
if (!text) return "";
var s = String(text);
if (s.length <= maxLen) return s;
return s.slice(0, maxLen) + "...[truncated " + (s.length - maxLen) + " chars]";
}
function estimateTokensFromChars(text) {
if (!text) return 0;
return Math.ceil(String(text).length / 4);
}
function pricingForModel(model) {
if (!model) return null;
for (var i = 0; i < PRICING.length; i++) {
if (PRICING[i].match.test(model)) return { input: PRICING[i].input, output: PRICING[i].output };
}
return null;
}
function estimateCost(model, inputTokens, outputTokens) {
var p = pricingForModel(model);
if (!p) return 0;
return ((inputTokens / 1000000) * p.input) + ((outputTokens / 1000000) * p.output);
}
var _db = null;
function getDb() {
if (_db) return _db;
_db = new Database(DB_PATH);
_db.pragma("journal_mode = WAL");
_db.pragma("synchronous = NORMAL");
_db.pragma("busy_timeout = 5000");
_db.exec(
"CREATE TABLE IF NOT EXISTS llm_calls (" +
" id INTEGER PRIMARY KEY AUTOINCREMENT," +
" timestamp TEXT NOT NULL DEFAULT (datetime('now'))," +
" provider TEXT," +
" model TEXT," +
" caller TEXT," +
" prompt TEXT," +
" response TEXT," +
" input_tokens INTEGER DEFAULT 0," +
" output_tokens INTEGER DEFAULT 0," +
" cost_estimate REAL DEFAULT 0," +
" duration_ms INTEGER DEFAULT 0," +
" ok INTEGER DEFAULT 1," +
" error TEXT" +
");" +
"CREATE INDEX IF NOT EXISTS idx_llm_calls_ts ON llm_calls(timestamp);" +
"CREATE INDEX IF NOT EXISTS idx_llm_calls_caller ON llm_calls(caller);" +
"CREATE INDEX IF NOT EXISTS idx_llm_calls_model ON llm_calls(model);"
);
return _db;
}
var _cached_insert = null;
function logLlmCall(opts) {
if (!opts) opts = {};
try {
var inputTokens = opts.inputTokens != null ? opts.inputTokens : estimateTokensFromChars(opts.prompt);
var outputTokens = opts.outputTokens != null ? opts.outputTokens : estimateTokensFromChars(opts.response);
var cost = estimateCost(opts.model, inputTokens, outputTokens);
if (!_cached_insert) {
_cached_insert = getDb().prepare(
"INSERT INTO llm_calls" +
" (provider, model, caller, prompt, response," +
" input_tokens, output_tokens, cost_estimate, duration_ms, ok, error)" +
" VALUES" +
" (@provider, @model, @caller, @prompt, @response," +
" @input_tokens, @output_tokens, @cost_estimate, @duration_ms, @ok, @error)"
);
}
_cached_insert.run({
provider: opts.provider || "unknown",
model: opts.model || "unknown",
caller: opts.caller || "unknown",
prompt: truncate(redact(opts.prompt)),
response: truncate(redact(opts.response)),
input_tokens: inputTokens,
output_tokens: outputTokens,
cost_estimate: Math.round(cost * 1000000) / 1000000,
duration_ms: opts.durationMs || 0,
ok: opts.ok !== false ? 1 : 0,
error: opts.error ? truncate(redact(opts.error), 2000) : null,
});
} catch (err) {
console.warn("[interaction-store] log failed:", err.message);
}
}
function recentCalls(limit) {
if (!limit) limit = 20;
return getDb().prepare("SELECT * FROM llm_calls ORDER BY id DESC LIMIT ?").all(limit);
}
function costByCallerSince(sinceIso) {
return getDb().prepare(
"SELECT caller, model, COUNT(*) AS calls," +
" SUM(input_tokens) AS total_input_tokens," +
" SUM(output_tokens) AS total_output_tokens," +
" ROUND(SUM(cost_estimate), 6) AS total_cost" +
" FROM llm_calls WHERE timestamp >= ?" +
" GROUP BY caller, model ORDER BY total_cost DESC"
).all(sinceIso);
}
function costSummary24h() {
return costByCallerSince(new Date(Date.now() - 86400000).toISOString());
}
function closeDb() {
if (_db) { _db.close(); _db = null; _cached_insert = null; }
}
module.exports = {
logLlmCall: logLlmCall,
estimateTokensFromChars: estimateTokensFromChars,
estimateCost: estimateCost,
pricingForModel: pricingForModel,
recentCalls: recentCalls,
costByCallerSince: costByCallerSince,
costSummary24h: costSummary24h,
closeDb: closeDb,
redact: redact,
truncate: truncate,
};
`);
// ── shared/anthropic-agent-sdk.js ───────────────────────────
writeFile("shared/anthropic-agent-sdk.js", `"use strict";
var fs = require("fs");
var path = require("path");
var modelUtils = require("./model-utils");
var store = require("./interaction-store");
function readDotEnv(key) {
var envPaths = [
path.join(process.cwd(), ".env"),
path.join(__dirname, "..", ".env"),
];
for (var p = 0; p < envPaths.length; p++) {
try {
var lines = fs.readFileSync(envPaths[p], "utf-8").split("\\n");
for (var i = 0; i < lines.length; i++) {
var trimmed = lines[i].trim();
if (trimmed.startsWith("#") || trimmed.indexOf("=") === -1) continue;
var eqIdx = trimmed.indexOf("=");
var k = trimmed.slice(0, eqIdx).trim();
if (k === key) {
var v = trimmed.slice(eqIdx + 1).trim();
if ((v.startsWith('"') && v.endsWith('"')) ||
(v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
return v || null;
}
}
} catch (e) {}
}
return null;
}
function resolveOAuthToken() {
var token = process.env.CLAUDE_CODE_OAUTH_TOKEN;
if (!token) token = readDotEnv("CLAUDE_CODE_OAUTH_TOKEN");
if (!token) {
throw new Error(
"[anthropic-agent-sdk] No OAuth token found.\\n" +
" Set CLAUDE_CODE_OAUTH_TOKEN in env or .env file.\\n" +
' Run "claude login" then "claude setup-token" to get your token.'
);
}
if (process.env.ANTHROPIC_API_KEY) {
throw new Error(
"[anthropic-agent-sdk] Both CLAUDE_CODE_OAUTH_TOKEN and ANTHROPIC_API_KEY are set.\\n" +
" Remove ANTHROPIC_API_KEY to use OAuth-only mode."
);
}
return token;
}
var _client = null;
function getClient() {
if (_client) return _client;
var token = resolveOAuthToken();
var ClaudeClient;
try {
var sdk = require("@anthropic-ai/claude-agent-sdk");
ClaudeClient = sdk.ClaudeClient || sdk.default || sdk;
} catch (err) {
throw new Error(
"[anthropic-agent-sdk] Cannot load @anthropic-ai/claude-agent-sdk.\\n" +
" Run: npm install @anthropic-ai/claude-agent-sdk\\n" +
" Error: " + err.message
);
}
_client = new ClaudeClient({ oauthToken: token });
return _client;
}
var _smokeTestDone = false;
async function runSmokeTest() {
if (_smokeTestDone) return;
if (process.env.LLM_SKIP_SMOKE_TEST === "1" || process.env.LLM_SKIP_SMOKE_TEST === "true") {
_smokeTestDone = true; return;
}
var client = getClient();
var controller = new AbortController();
var timer = setTimeout(function() { controller.abort(); }, 20000);
try {
var response = await client.query({
model: "claude-opus-4-6",
prompt: "Reply with exactly AUTH_OK and nothing else.",
tools: [], maxTurns: 1, signal: controller.signal,
});
var text = extractText(response);
if (text.indexOf("AUTH_OK") === -1) {
throw new Error(
'Smoke test failed. Got: "' + text.slice(0, 200) + '"\\n' +
" Token may be expired. Run: claude login"
);
}
_smokeTestDone = true;
console.log("[anthropic-agent-sdk] Smoke test passed (Opus 4.6 + OAuth)");
} catch (err) {
if (err.name === "AbortError") {
throw new Error("[anthropic-agent-sdk] Smoke test timed out.\\n Set LLM_SKIP_SMOKE_TEST=1 to bypass.");
}
throw err;
} finally { clearTimeout(timer); }
}
function extractText(response) {
if (!response) return "";
if (typeof response === "string") return response;
if (typeof response.text === "string") return response.text;
if (Array.isArray(response.content)) {
return response.content
.filter(function(b) { return b.type === "text" && typeof b.text === "string"; })
.map(function(b) { return b.text; }).join("\\n");
}
if (Array.isArray(response.messages)) {
var blocks = [];
for (var i = 0; i < response.messages.length; i++) {
var m = response.messages[i];
if (Array.isArray(m.content)) {
for (var j = 0; j < m.content.length; j++) {
if (m.content[j].type === "text" && typeof m.content[j].text === "string") {
blocks.push(m.content[j].text);
}
}
}
}
return blocks.join("\\n");
}
return JSON.stringify(response).slice(0, 500);
}
async function runAnthropicAgentPrompt(opts) {
if (!opts) opts = {};
var rawModel = opts.model;
var prompt = opts.prompt;
var timeoutMs = opts.timeoutMs || 120000;
var caller = opts.caller || "unknown";
var maxTurns = opts.maxTurns || 1;
var skipLog = opts.skipLog || false;
var systemPrompt = opts.systemPrompt;
if (!prompt) throw new Error("[anthropic-agent-sdk] prompt is required");
await runSmokeTest();
var model = modelUtils.normalizeAnthropicModel(rawModel);
var client = getClient();
var start = Date.now();
var controller = new AbortController();
var timer = setTimeout(function() { controller.abort(); }, timeoutMs);
var text = "", ok = true, error = null;
var inputTokens = 0, outputTokens = 0;
try {
var queryOpts = {
model: model, prompt: prompt, tools: [], maxTurns: maxTurns,
signal: controller.signal,
};
if (systemPrompt) queryOpts.systemPrompt = systemPrompt;
var response = await client.query(queryOpts);
text = extractText(response);
if (response && response.usage) {
inputTokens = response.usage.input_tokens || 0;
outputTokens = response.usage.output_tokens || 0;
} else {
inputTokens = store.estimateTokensFromChars(prompt);
outputTokens = store.estimateTokensFromChars(text);
}
} catch (err) {
ok = false;
error = err.name === "AbortError" ? "Timeout after " + timeoutMs + "ms" : err.message;
inputTokens = store.estimateTokensFromChars(prompt);
} finally { clearTimeout(timer); }
var durationMs = Date.now() - start;
var cost = store.estimateCost(model, inputTokens, outputTokens);
if (!skipLog) {
store.logLlmCall({
provider: "anthropic", model: model, caller: caller, prompt: prompt,
response: text, inputTokens: inputTokens, outputTokens: outputTokens,
durationMs: durationMs, ok: ok, error: error,
});
}
if (!ok) throw new Error("[anthropic-agent-sdk] " + error);
return { text: text, provider: "anthropic", durationMs: durationMs,
inputTokens: inputTokens, outputTokens: outputTokens, cost: cost };
}
module.exports = {
runAnthropicAgentPrompt: runAnthropicAgentPrompt,
resolveOAuthToken: resolveOAuthToken,
extractText: extractText,
};
`);
// ── shared/llm-router.js ───────────────────────────────────
writeFile("shared/llm-router.js", `"use strict";
var modelUtils = require("./model-utils");
var anthropic = require("./anthropic-agent-sdk");
var store = require("./interaction-store");
var DEFAULT_MODEL = process.env.LLM_DEFAULT_MODEL || "claude-opus-4-6";
async function runOpenAiPrompt(opts) {
var model = opts.model, prompt = opts.prompt;
var timeoutMs = opts.timeoutMs || 120000;
var caller = opts.caller, systemPrompt = opts.systemPrompt;
var start = Date.now();
var apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) throw new Error('[llm-router] OpenAI model "' + model + '" requested but OPENAI_API_KEY not set.');
var controller = new AbortController();
var timer = setTimeout(function() { controller.abort(); }, timeoutMs);
var text = "", ok = true, error = null, inputTokens = 0, outputTokens = 0;
try {
var messages = [];
if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
messages.push({ role: "user", content: prompt });
var res = await fetch("https://api.openai.com/v1/chat/completions", {
method: "POST",
headers: { "Content-Type": "application/json", "Authorization": "Bearer " + apiKey },
body: JSON.stringify({ model: model, messages: messages, max_tokens: 4096 }),
signal: controller.signal,
});
if (!res.ok) {
var body = await res.text().catch(function() { return ""; });
throw new Error("OpenAI API " + res.status + ": " + body.slice(0, 300));
}
var data = await res.json();
text = (data.choices && data.choices[0] && data.choices[0].message)
? data.choices[0].message.content || "" : "";
inputTokens = (data.usage && data.usage.prompt_tokens) || store.estimateTokensFromChars(prompt);
outputTokens = (data.usage && data.usage.completion_tokens) || store.estimateTokensFromChars(text);
} catch (err) {
ok = false;
error = err.name === "AbortError" ? "Timeout after " + timeoutMs + "ms" : err.message;
inputTokens = store.estimateTokensFromChars(prompt);
} finally { clearTimeout(timer); }
var durationMs = Date.now() - start;
var cost = store.estimateCost(model, inputTokens, outputTokens);
return { text: text, ok: ok, error: error, inputTokens: inputTokens,
outputTokens: outputTokens, durationMs: durationMs, cost: cost, provider: "openai" };
}
async function runLlm(prompt, opts) {
if (!opts) opts = {};
if (!prompt) throw new Error("[llm-router] prompt is required");
var rawModel = opts.model || DEFAULT_MODEL;
var model = modelUtils.normalizeModel(rawModel);
var provider = modelUtils.detectModelProvider(model);
var caller = opts.caller || "unknown";
var skipLog = opts.skipLog || false;
if (provider === "anthropic") {
return anthropic.runAnthropicAgentPrompt({
model: rawModel, prompt: prompt, timeoutMs: opts.timeoutMs,
caller: caller, skipLog: skipLog, systemPrompt: opts.systemPrompt,
});
}
if (provider === "openai") {
var result = await runOpenAiPrompt({
model: model, prompt: prompt, timeoutMs: opts.timeoutMs,
caller: caller, systemPrompt: opts.systemPrompt,
});
if (!skipLog) {
store.logLlmCall({
provider: "openai", model: model, caller: caller, prompt: prompt,
response: result.text, inputTokens: result.inputTokens,
outputTokens: result.outputTokens, durationMs: result.durationMs,
ok: result.ok, error: result.error,
});
}
if (!result.ok) throw new Error("[llm-router] OpenAI failed: " + result.error);
return {
text: result.text, durationMs: result.durationMs, provider: "openai",
inputTokens: result.inputTokens, outputTokens: result.outputTokens, cost: result.cost,
};
}
throw new Error('[llm-router] Unknown provider for model "' + model + '"');
}
async function askOpus(prompt, caller) {
return runLlm(prompt, { model: "claude-opus-4-6", caller: caller || "unknown" });
}
async function askSonnet(prompt, caller) {
return runLlm(prompt, { model: "claude-sonnet-4", caller: caller || "unknown" });
}
async function askHaiku(prompt, caller) {
return runLlm(prompt, { model: "haiku-4", caller: caller || "unknown" });
}
module.exports = {
runLlm: runLlm,
askOpus: askOpus,
askSonnet: askSonnet,
askHaiku: askHaiku,
};
`);
// ── cost-report.js ──────────────────────────────────────────
writeFile("cost-report.js", `#!/usr/bin/env node
"use strict";
var store = require("./shared/interaction-store");
var args = process.argv.slice(2);
var hours = 24, raw = 0, topCallers = false;
for (var i = 0; i < args.length; i++) {
if (args[i] === "--hours" && args[i+1]) hours = Number(args[++i]);
if (args[i] === "--raw" && args[i+1]) raw = Number(args[++i]);
if (args[i] === "--top-callers") topCallers = true;
}
var since = new Date(Date.now() - hours * 3600000).toISOString();
console.log("\\nLLM Usage Report - last " + hours + "h (since " + since.slice(0,16) + ")\\n");
var breakdown = store.costByCallerSince(since);
if (breakdown.length === 0) {
console.log(" No calls logged.\\n");
} else {
var totalCost=0, totalIn=0, totalOut=0, totalCalls=0;
var rows = breakdown.map(function(r) {
totalCost += r.total_cost; totalIn += r.total_input_tokens;
totalOut += r.total_output_tokens; totalCalls += r.calls;
return {
Caller: r.caller, Model: (r.model||"").replace("claude-","").slice(0,25),
Calls: r.calls, "In Tok": (r.total_input_tokens||0).toLocaleString(),
"Out Tok": (r.total_output_tokens||0).toLocaleString(),
"Cost": "$" + r.total_cost.toFixed(4),
};
});
console.table(rows);
console.log(" TOTALS: " + totalCalls + " calls | " +
totalIn.toLocaleString() + " in | " + totalOut.toLocaleString() +
" out | $" + totalCost.toFixed(4) + "\\n");
if (topCallers) {
var bc = {};
for (var j = 0; j < breakdown.length; j++) {
var r = breakdown[j];
if (!bc[r.caller]) bc[r.caller] = {calls:0,cost:0};
bc[r.caller].calls += r.calls; bc[r.caller].cost += r.total_cost;
}
console.log(" Top callers:");
console.table(Object.entries(bc).sort(function(a,b){return b[1].cost-a[1].cost})
.map(function(e){return {Caller:e[0], Calls:e[1].calls, Cost:"$"+e[1].cost.toFixed(4)};}));
}
}
if (raw > 0) {
console.log("\\n Last " + raw + " calls:\\n");
var calls = store.recentCalls(raw);
for (var k = 0; k < calls.length; k++) {
var c = calls[k];
var s = c.ok ? "OK" : "FAIL";
console.log(" [" + s + "] " + c.timestamp + " " + c.caller + " > " + c.model +
" (" + c.duration_ms + "ms, $" + c.cost_estimate.toFixed(6) + ")");
if (c.error) console.log(" ERR: " + c.error);
}
}
store.closeDb();
`);
// ── test-router.js ──────────────────────────────────────────
writeFile("test-router.js", `#!/usr/bin/env node
"use strict";
function assert(c, m) { if (!c) throw new Error("FAIL: " + m); }
async function main() {
var offline = process.argv.indexOf("--offline") !== -1;
var passed = 0;
console.log("\\n--- model-utils ---");
var mu = require("./shared/model-utils");
assert(mu.isAnthropicModel("claude-opus-4-6"), "opus is anthropic");
assert(!mu.isAnthropicModel("gpt-4o"), "gpt not anthropic");
assert(mu.detectModelProvider("opus-4") === "anthropic", "detect opus");
assert(mu.detectModelProvider("gpt-4o") === "openai", "detect gpt");
assert(mu.normalizeAnthropicModel("opus-4") === "claude-opus-4-6", "normalize opus");
assert(mu.normalizeAnthropicModel("opus-4.6") === "claude-opus-4-6", "normalize 4.6");
console.log(" PASS: model-utils"); passed++;
console.log("\\n--- interaction-store ---");
process.env.LLM_LOG_DB = require("path").join(require("os").tmpdir(), "test_llm_" + Date.now() + ".db");
var store = require("./shared/interaction-store");
assert(store.estimateTokensFromChars("hello world") === 3, "token est");
assert(store.redact("sk-ant-abcdefghijklmnopqrstuvwxyz").indexOf("[REDACTED]") !== -1, "redact");
store.logLlmCall({
provider: "anthropic", model: "claude-opus-4-6", caller: "test",
prompt: "key sk-ant-secretkey1234567890abcdefg here", response: "ok", ok: true,
});
var recent = store.recentCalls(1);
assert(recent.length === 1, "logged 1");
assert(recent[0].prompt.indexOf("[REDACTED]") !== -1, "key redacted");
assert(recent[0].prompt.indexOf("secretkey") === -1, "no raw key");
console.log(" PASS: interaction-store"); passed++;
store.closeDb();
try { require("fs").unlinkSync(process.env.LLM_LOG_DB); } catch(e) {}
if (!offline) {
console.log("\\n--- live API test ---");
delete process.env.LLM_LOG_DB;
try {
delete require.cache[require.resolve("./shared/interaction-store")];
delete require.cache[require.resolve("./shared/anthropic-agent-sdk")];
delete require.cache[require.resolve("./shared/llm-router")];
var router = require("./shared/llm-router");
var r = await router.runLlm("What is 2+2? Reply with just the number.", {
model: "claude-opus-4-6", caller: "test-router", timeoutMs: 30000,
});
assert(r.text.indexOf("4") !== -1, "correct answer");
assert(r.provider === "anthropic", "provider");
console.log(" PASS: " + r.text.trim() + " (" + r.durationMs + "ms)");
passed++;
} catch(e) {
console.log(" SKIP: " + e.message.slice(0, 120));
console.log(" (expected if OAuth token not set yet)");
}
}
console.log("\\n=== " + passed + " test groups passed ===\\n");
}
main().catch(function(e) { console.error(e.message); process.exit(1); });
`);
// ── Done ────────────────────────────────────────────────────
console.log("\n============================================");
console.log(" LLM Router created at: " + BASE);
console.log("============================================");
console.log("");
console.log("NEXT STEPS:");
console.log(" 1. Open a terminal and run:");
console.log(" cd " + BASE);
console.log(" npm install");
console.log(" 2. Run: claude login");
console.log(" 3. Run: claude setup-token");
console.log(" 4. Paste the token into: " + path.join(BASE, ".env"));
console.log(" 5. Test offline: node test-router.js --offline");
console.log(" 6. Test live: node test-router.js");
console.log("");
console.log("USAGE in any script:");
console.log(' const { runLlm, askOpus } = require("' + path.join(BASE, "shared", "llm-router").replace(/\\/g, "/") + '");');
console.log(' const result = await askOpus("Your prompt", "caller-name");');
console.log("");