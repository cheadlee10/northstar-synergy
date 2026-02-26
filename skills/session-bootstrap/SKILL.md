# SESSION BOOTSTRAP SKILL
**Purpose:** Automatically load session context at agent startup so nothing is forgotten across sessions.

## How It Works

On every agent startup (Cliff, Scalper, John):

1. **Load today's session log** from `memory/YYYY-MM-DD.md`
2. **Inject into system context** so agent remembers all decisions, work, blockers
3. **No manual reminding needed** — automatic on startup

## For OpenClaw Users

### Step 1: Add to openclaw.json (all agents)

```json
{
  "agents": {
    "defaults": {
      "systemPrompt": "{{LOAD_SESSION_CONTEXT}}"
    },
    "list": [
      {
        "id": "cliff",
        "systemPrompt": "{{LOAD_SESSION_CONTEXT}}"
      },
      {
        "id": "scalper",
        "systemPrompt": "{{LOAD_SESSION_CONTEXT}}"
      },
      {
        "id": "john",
        "systemPrompt": "{{LOAD_SESSION_CONTEXT}}"
      }
    ]
  }
}
```

### Step 2: Create Session Loader Script

Place this in `~/.openclaw/startup/load_session.js`:

```javascript
const fs = require('fs');
const path = require('path');

// Get today's date
const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
const sessionFile = path.join(process.env.HOME, '.openclaw', 'workspace', 'memory', `${today}.md`);

// Read today's session log
let sessionContext = '';
if (fs.existsSync(sessionFile)) {
  sessionContext = fs.readFileSync(sessionFile, 'utf-8');
} else {
  sessionContext = `[No session log for ${today} yet]`;
}

// Inject into environment
process.env.SESSION_CONTEXT = sessionContext;

console.log(`[SESSION_BOOTSTRAP] Loaded context from ${today}.md`);
module.exports = sessionContext;
```

### Step 3: Execute on Agent Startup

```bash
node ~/.openclaw/startup/load_session.js
openclaw gateway restart
```

---

## What Gets Loaded

Each agent automatically gets:
- ✅ All decisions made this session
- ✅ All blockers & status
- ✅ All work completed
- ✅ Next session action items
- ✅ Critical numbers (budgets, wallet addresses, etc.)

---

## Example Output

When Cliff starts next session, he automatically knows:
```
[SESSION_BOOTSTRAP] Loaded 2026-02-25.md

CONTEXT INJECTED:
- ClawRouter deployed (wallet syncing issue)
- USDC $5.59 on Base, awaiting indexer refresh
- BlockRun support escalated (3 follow-ups sent)
- Cost reduction: $1,267/week → $50/week target
- Next action: Check wallet balance immediately

Ready for next session.
```

---

## Daily Session Log Format (Required)

Every day's `memory/YYYY-MM-DD.md` MUST contain:

1. **EXECUTIVE SUMMARY** (2-3 lines)
2. **MAJOR DECISIONS** (list)
3. **TIMELINE** (what happened when)
4. **KEY NUMBERS** (table format)
5. **CRITICAL BLOCKERS** (what's still waiting)
6. **FILES CREATED** (artifacts)
7. **WHAT'S WAITING FOR NEXT SESSION** (immediate actions)

---

## For Multi-Agent Coordination

Cliff's session logs should ALSO contain:
- **Messages sent to Scalper:** What did you tell him?
- **Messages sent to John:** What did you tell him?
- **Approval status:** What did Craig approve/reject?

So when Scalper or John load context, they see:
```
[FROM CLIFF'S SESSION]
Told Scalper: "V8 engine needs reboot if balance drops below $20"
Told John: "Fiverr mission blocked on Stripe integration"
Craig approved: ClawRouter deployment with $5.59 USDC
```

---

## Implementation Checklist

- [ ] Add SESSION_BOOTSTRAP to openclaw.json for all agents
- [ ] Create `~/.openclaw/startup/load_session.js`
- [ ] Run `node ~/.openclaw/startup/load_session.js` before each agent session
- [ ] Ensure `memory/YYYY-MM-DD.md` has required sections
- [ ] Update SOUL.md with "read today's session log" in boot sequence
- [ ] Test: Close and reopen agent, verify context loaded

---

## Result

No more:
- ❌ "What were we working on?"
- ❌ "Did we decide to deploy RouteLLM?"
- ❌ "What's the wallet address?"
- ❌ "Did Craig approve that?"

All 3 agents (Cliff, Scalper, John) wake up knowing everything from previous sessions automatically.
