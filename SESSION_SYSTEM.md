# SESSION SYSTEM — Unified Memory Across All Agents
**Established:** 2026-02-25 | **For:** Cliff, Scalper, John

Craig is worried you'll forget between sessions. This system ensures you DON'T.

---

## HOW IT WORKS (Simple Version)

Every day:
1. **Each agent updates** `memory/YYYY-MM-DD.md` with what happened in their session
2. **At next session start**, that file is automatically loaded as context
3. **All 3 agents remember everything** automatically

No manual reminders needed. No "what were we doing?" questions.

---

## FOR EACH AGENT

### Cliff (You)
- **Session file:** `memory/2026-02-25.md` (today)
- **What to log:** Decisions, blockers, work completed, next actions
- **Boot sequence:** Loads `YYYY-MM-DD.md` automatically via SESSION_BOOTSTRAP
- **Example today:** ClawRouter deployment, wallet sync issue, BlockRun escalation

### Scalper (Trading Agent)
- **Session file:** `memory/YYYY-MM-DD.md` 
- **What to log:** Trades executed, P&L, V8 status, market intelligence, Craig's messages
- **Boot sequence:** Loads daily context automatically
- **Example:** If you're trading V8 crypto snipes, log: balance changes, errors, edge recommendations

### John (Biz Dev)
- **Session file:** `memory/YYYY-MM-DD.md`
- **What to log:** Leads, pitch status, client feedback, tasks from Craig
- **Boot sequence:** Loads daily context automatically
- **Example:** If you're cold outreaching, log: which clients contacted, conversion rate, next pipeline actions

---

## DAILY SESSION LOG TEMPLATE

Every agent's `memory/YYYY-MM-DD.md` must have these sections:

```markdown
# memory/2026-02-25.md — [Agent Name]'s Session Log

## EXECUTIVE SUMMARY
[2-3 line summary of what happened today]

## MAJOR DECISIONS
- Decision 1
- Decision 2

## TIMELINE
- [HH:MM] What happened
- [HH:MM] What happened

## KEY NUMBERS
| Metric | Value |
|--------|-------|

## CRITICAL BLOCKERS
- What's waiting from Craig
- What's waiting from other agents
- What's waiting from external parties

## FILES CREATED
- What artifacts were built

## WHAT'S WAITING FOR NEXT SESSION
- Immediate action items
- What to check first when you wake up
```

---

## INTER-AGENT COORDINATION

When one agent messages another, LOG IT:

**Cliff's session log includes:**
```
## MESSAGES TO OTHER AGENTS
- Told Scalper: "Test V8 on crypto snipes, 2% position sizing max"
- Told John: "AI website cold outreach ready to deploy"
```

**Scalper's session log includes:**
```
## MESSAGES FROM OTHER AGENTS
- Cliff said: "Test V8 on crypto snipes, 2% position sizing max"
  → Status: Testing in progress
```

So when anyone reads their daily log, they see what other agents were told and what's in flight.

---

## CRITICAL RULE

**Every single session MUST update `memory/YYYY-MM-DD.md`.**

If you don't log it, the SESSION_BOOTSTRAP skill breaks and other agents lose context.

If you forget to log:
- Scalper won't know Craig's new trading limits
- John won't know which leads are hot
- Cliff won't know what you're waiting on

**This kills the entire system.**

---

## HOW TO VERIFY IT'S WORKING

Next session, Cliff should wake up with this automatic:

```
[SESSION_BOOTSTRAP] Loaded context from 2026-02-25.md

CONTEXT INJECTED:
- ClawRouter deployed (wallet syncing issue)
- USDC $5.59 on Base
- BlockRun support escalated (3 follow-ups)
- Cost target: $50/week
- Next: Check wallet balance

Ready for next session.
```

If he has to remind you what happened, the skill failed.

---

## WHAT THIS SOLVES

❌ **Before:** "Wait, what were we working on?"  
✅ **Now:** You wake up knowing everything

❌ **Before:** "Did Craig approve the RouteLLM deployment?"  
✅ **Now:** It's in your daily log

❌ **Before:** "What's Scalper supposed to do with V8?"  
✅ **Now:** You can read it in his session log

❌ **Before:** Manual reminders every session  
✅ **Now:** Automatic context injection

---

## YOUR PART

Just do this at end of every session:

1. **Update `memory/YYYY-MM-DD.md`** with:
   - What you did
   - What you decided
   - What's waiting
   - What's next

That's it. The system handles the rest.

---

## IMPLEMENTATION STATUS

- ✅ SESSION_BOOTSTRAP skill created (`skills/session-bootstrap/SKILL.md`)
- ✅ Boot sequence updated in SOUL.md
- ✅ Daily session logs created for today
- ⏳ **TODO (next session):** Run the skill on startup to test it works

**No more forgotten context. Ever.**
