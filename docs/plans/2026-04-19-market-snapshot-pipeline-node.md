# Market Snapshot Pipeline Node Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a composable `market_snapshot` pipeline node that enriches market-facing requests with live price and per-asset news headlines before the final response.

**Architecture:** Extend the existing router-ready single-runtime pipeline with one more pre-response node. The node stays read-only, resolves its symbol from chart observations or market context, gathers `get_price` and `search_news_by_symbols` data, and injects trusted backend observations into the final runtime prompt.

**Tech Stack:** Python, Pydantic, pytest, existing tool registry, Mintlify `.doch`

---

### Task 1: Add pipeline planning for `market_snapshot`

**Files:**
- Modify: `agents/core/pipeline.py`
- Test: `test/agents/test_agent_pipeline.py`

Add a new pipeline node constant, a planner rule for market-facing requests, and include the node before `response_composer`.

### Task 2: Implement the runtime node

**Files:**
- Create: `agents/nodes/market_snapshot.py`
- Modify: `agents/core/graph_executor.py`
- Test: `test/agents/test_market_snapshot_node.py`

Build a read-only node that resolves the best symbol, fetches price and news, normalizes the output, and returns a trusted prompt addition plus trace metadata.

### Task 3: Prove integration through the existing agent

**Files:**
- Modify: `test/agents/test_agent_pipeline.py`
- Modify: `test/agents/test_multimodal_agent_payloads.py`

Update pipeline integration assertions so chart-heavy market requests prove that:
- `chart_analysis` runs first
- `market_snapshot` runs next
- the main runtime still receives a restricted tool schema

### Task 4: Update docs

**Files:**
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/features/agent/index.mdx`
- Modify: `.doch/tools/market/index.mdx`

Document the new node so the current architecture reflects the actual pipeline:
- `market_specialist` remains the selected target
- chart analysis is a technical sub-step
- market snapshot is the context-enrichment sub-step
