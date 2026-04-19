# Chart Analysis Pipeline Node Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a composable chart-analysis pipeline node that can run inside the existing agent entrypoint without hardcoding a second runtime.

**Architecture:** The existing `TradingAgent` remains the API entrypoint, but after intent routing it will execute a graph-like plan made of pipeline nodes. The first specialist-ready node is `chart_analysis`, which uses a bounded Reason → Act → Critique → Observe loop and strict guardrails around symbol changes and TradingView tool scope.

**Tech Stack:** Python, Pydantic, existing BaseAgent/TradingAgent runtime, TradingView tools, pytest, Mintlify docs.

---

### Task 1: Extend pipeline models to support composable nodes

**Files:**
- Modify: `agents/core/pipeline.py`
- Test: `test/agents/test_agent_pipeline.py`

**Step 1: Write the failing test**

Add tests that assert:
- a chart-oriented intent can plan `pipeline_nodes`
- the plan contains `chart_analysis` followed by `response_composer`

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\agents\test_agent_pipeline.py -q`
Expected: FAIL because `pipeline_nodes` planning does not exist yet.

**Step 3: Write minimal implementation**

Add:
- `AgentPipelineNodePlan`
- `build_pipeline_nodes(...)`
- pipeline trace support for storing node plans

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\agents\test_agent_pipeline.py -q`
Expected: PASS for the new planning test.

**Step 5: Commit**

```bash
git add agents/core/pipeline.py test/agents/test_agent_pipeline.py docs/plans/2026-04-19-chart-analysis-pipeline-node.md
git commit -m "feat: add composable pipeline node planning"
```

### Task 2: Add graph executor primitives

**Files:**
- Create: `agents/core/graph_executor.py`
- Modify: `agents/core/base.py`
- Test: `test/agents/test_agent_pipeline.py`

**Step 1: Write the failing test**

Add tests that assert:
- the executor can run a simple node sequence
- node results are recorded into pipeline metadata

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\agents\test_agent_pipeline.py -q`
Expected: FAIL because graph execution does not exist.

**Step 3: Write minimal implementation**

Create:
- `AgentPipelineNodeResult`
- `AgentPipelineNode`
- `AgentGraphExecutor`

Wire it into `BaseAgent` without changing API request shape.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\agents\test_agent_pipeline.py -q`
Expected: PASS for executor coverage.

**Step 5: Commit**

```bash
git add agents/core/graph_executor.py agents/core/base.py test/agents/test_agent_pipeline.py
git commit -m "feat: add agent graph executor primitives"
```

### Task 3: Implement chart analysis node

**Files:**
- Create: `agents/nodes/chart_analysis.py`
- Modify: `agents/core/base.py`
- Test: `test/agents/test_chart_analysis_node.py`

**Step 1: Write the failing test**

Add tests that assert:
- locked asset blocks symbol changes
- global scope allows symbol changes
- the node can add indicator then read indicator values
- the node never uses drawing/alert tools

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\agents\test_chart_analysis_node.py -q`
Expected: FAIL because the chart node does not exist.

**Step 3: Write minimal implementation**

Implement:
- bounded `Reason → Act → Critique → Observe` loop
- tool whitelist
- temporary-indicator tracking
- symbol-change guardrails

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\agents\test_chart_analysis_node.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add agents/nodes/chart_analysis.py test/agents/test_chart_analysis_node.py agents/core/base.py
git commit -m "feat: add chart analysis pipeline node"
```

### Task 4: Integrate chart node into pipeline trace and fallback behavior

**Files:**
- Modify: `agents/core/base.py`
- Modify: `api/models.py`
- Modify: `api/routes.py`
- Test: `test/api/test_agent_stream_routes.py`
- Test: `test/agents/test_agent_fallbacks.py`

**Step 1: Write the failing test**

Add tests that assert:
- API `agent_pipeline` includes `pipeline_nodes`
- chart node errors degrade gracefully
- fallback metadata is visible in the trace

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\api\test_agent_stream_routes.py test\agents\test_agent_fallbacks.py -q`
Expected: FAIL because node-level trace metadata is incomplete.

**Step 3: Write minimal implementation**

Expose:
- planned nodes
- executed nodes
- node-level degradation/fallback metadata

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\api\test_agent_stream_routes.py test\agents\test_agent_fallbacks.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add agents/core/base.py api/models.py api/routes.py test/api/test_agent_stream_routes.py test/agents/test_agent_fallbacks.py
git commit -m "feat: surface chart node pipeline trace in api responses"
```

### Task 5: Update documentation

**Files:**
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/features/agent/index.mdx`
- Modify: `.doch/tools/tradingview/index.mdx`

**Step 1: Write the docs update**

Document:
- composable node planning
- chart analysis node boundaries
- allowed TradingView operations
- asset-lock behavior

**Step 2: Validate docs references**

Run: `rg -n "chart_analysis|pipeline_nodes|Reason" .doch`
Expected: updated pages contain the new flow.

**Step 3: Commit**

```bash
git add .doch/agents/index.mdx .doch/agents/routing/intent-routing.mdx .doch/features/agent/index.mdx .doch/tools/tradingview/index.mdx
git commit -m "docs: describe chart analysis pipeline node"
```

### Task 6: Final verification

**Files:**
- Test: `test/agents/test_agent_pipeline.py`
- Test: `test/agents/test_chart_analysis_node.py`
- Test: `test/agents/test_agent_fallbacks.py`
- Test: `test/api/test_agent_stream_routes.py`
- Test: `test/agents/test_multimodal_agent_payloads.py`

**Step 1: Run final targeted suite**

Run:

```bash
python -m pytest test\agents\test_agent_pipeline.py test\agents\test_chart_analysis_node.py test\agents\test_agent_fallbacks.py test\api\test_agent_stream_routes.py test\agents\test_multimodal_agent_payloads.py -q
```

Expected: PASS.

**Step 2: Commit final integration**

```bash
git add agents api test .doch docs/plans/2026-04-19-chart-analysis-pipeline-node.md
git commit -m "feat: add composable chart analysis pipeline node"
```
