# Athena Strategic Partner Upgrade Plan

## Goal
Transform Athena from a chatbot/secretary into a predictive strategic real estate partner that maxes out memory, provides deep analysis, and proactively drives business decisions.

---

## Phase 1: System Prompt Overhaul

**File: `packages/hermes/src/hermes/agent.py` — Replace `SYSTEM_PROMPT` (line 124-219)**

Key changes from current prompt:
1. **Role change**: "Digital Secretary" → "Strategic Real Estate Partner & AI Intelligence Engine"
2. **Verbosity mandate**: "You don't give one-line answers. Analyze, contextualize, compare, explain."
3. **Prediction requirement**: "Whenever you analyze data, offer at least one prediction."
4. **Response structure**: Every data response must have: 1) Raw data formatted cleanly, 2) Strategic analysis, 3) Recommended actions, 4) Predictive insight
5. **Memory usage**: "Auto-memorize key facts after every exchange. Predict-and-track: remember predictions, verify accuracy later."
6. **Cross-reference**: "Pull leads, then check their details. Pull listings, then check market position. Combine data."

The new prompt should be ~3x longer, with explicit sections:
- Strategic analysis requirements
- Prediction engine rules
- Memory maximization instructions
- Response formatting standards
- Tool usage strategy (call multiple tools for deeper insight)

---

## Phase 2: Memory Maximization

### 2a. Auto-Predict-and-Track (`agent.py` — `chat()` method, line ~600)

After each chat response, implicitly store:
- Key facts extracted from the response
- Any predictions made (lead conversion timeline, pricing recommendations)
- User decisions and preferences
- Context for future conversations

Store via `remember_fact()` or direct `athena_facts` INSERT:
```python
# After successful response, auto-memorize:
remember("last_prediction", f"Predicted {lead_name} conversion in {days} days on {date}")
remember("user_decision", f"User chose to {action} on {date}")
remember("pattern_observed", f"{pattern} detected in {context}")
```

### 2b. Prediction Verification (`tools.py` — new tool)

New tool: `verify_predictions()` — reviews past predictions against current data:
- Checks if leads predicted to convert actually did
- Tracks prediction accuracy
- Reports what was learned

### 2c. Weekly Consolidation (`memory.py`)

New function: `auto_consolidate(user_id)` — runs on first chat of the week:
- Summarizes last week's conversations into key insights
- Identifies patterns (lead sources that convert, listing types that move fast)
- Generates weekly performance metrics
- Stores as structured facts for future reference

---

## Phase 3: Strategic Analysis Tools

### 3a. `predict_lead_conversion(lead_id)` — New tool in `tools.py`
- Analyzes lead score trend, contact frequency, budget alignment
- Compares with similar converted leads
- Returns: conversion probability %, estimated timeline, confidence level
- Automatically saves prediction for later verification

### 3b. `analyze_market_position(property_id)` — New tool
- Compares listing to active comps in same city
- Ranks by price/sqft positioning
- Returns: competitive rank, suggested price adjustment, market heat level
- Flags overpriced listings and suggests corrections

### 3c. `detect_at_risk()` — New tool  
- Finds leads not contacted in 7+ days
- Finds listings with 0 showings in 14+ days
- Finds clients with expiring pre-approvals
- Returns prioritized risk list with recommended actions

### 3d. `pipeline_analysis()` — Enhance existing `analyze_pipeline`
- Add velocity metrics (avg days in stage)
- Add conversion probability per lead
- Add revenue projection based on pipeline value

---

## Phase 4: Verbosity & Response Quality

### 4a. Temperature & Model Parameters
Increase `temperature` from current value to 0.8 for more creative/expansive responses
Increase `max_tokens` to 4096 for longer strategic responses

### 4b. Post-Processing
Add a post-response enrichment step that:
- Checks if response is too short (< 200 chars for data requests)
- If so, appends strategic context: analysis, prediction, recommendation
- Formats consistently: bold names, bullet lists, section headers

---

## Phase 5: Proactive Intelligence

### 5a. Daily Briefing V2 (`main.py` — `briefing_v1`)
Enhance to include:
- Predictive insights from past data
- Risk alerts (leads at risk, listings stagnant)
- Opportunities (new leads matching client criteria)
- Market momentum indicators

### 5b. Trigger System (new)
Periodic checks (can be triggered by user or on schedule):
- "It's been 5 days since you contacted [lead] — time to follow up"
- "[Property] has been listed 30 days with no offers — consider price adjustment"
- "3 new leads match [client]'s criteria — notify them?"

---

## Implementation Order
1. ✅ System prompt rewrite (immediate — copy/paste to agent.py)
2. Temperature + max_tokens increase
3. Auto-memory: predict-and-track in chat() method
4. Strategic tools: predict_lead_conversion, detect_at_risk, analyze_market_position
5. Weekly consolidation
6. Briefing V2 with predictive insights

---

## Files to Change
1. `packages/hermes/src/hermes/agent.py` — SYSTEM_PROMPT (line 124), chat() method (line ~600), temperature/max_tokens
2. `packages/hermes/src/hermes/tools.py` — New tools: predict_lead_conversion, detect_at_risk, analyze_market_position, verify_predictions
3. `packages/hermes/src/hermes/memory.py` — auto_consolidate function
4. `apps/api/src/main.py` — briefing_v1 enhancement with predictive insights
