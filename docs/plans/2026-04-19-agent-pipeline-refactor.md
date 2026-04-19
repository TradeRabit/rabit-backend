# Agent Pipeline Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the current single-agent flow into a multi-agent-ready entrypoint pipeline with explicit routing trace, dispatch target selection, safer fallback behavior, and regression coverage.

**Architecture:** Keep one executable agent runtime for now, but split the request lifecycle into explicit stages: entrypoint, routing, dispatch planning, execution, and completion. The router remains the first classifier, but its output now feeds a dispatch plan that selects a future specialist target without instantiating specialist agents yet. API responses and SSE completion events expose the pipeline trace so mobile and future orchestration layers can rely on stable metadata.

**Tech Stack:** Python, FastAPI, Pydantic, Anthropic/OpenRouter client, pytest.

---

### Task 1: Add pipeline trace models

**Files:**
- Create: `agents/core/pipeline.py`
- Modify: `agents/core/__init__.py`
- Test: `test/agents/test_agent_pipeline.py`

**Step 1: Write the failing test**

Add tests for:
- specialist target resolution from intent
- fallback pipeline trace when router confidence is low
- serializable pipeline trace shape

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\\agents\\test_agent_pipeline.py -q`
Expected: FAIL because the module and helpers do not exist.

**Step 3: Write minimal implementation**

Add:
- `AgentPipelineStage`
- `AgentPipelineTrace`
- specialist target resolver
- helper to build a default trace from `AgentIntentContext`

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\\agents\\test_agent_pipeline.py -q`
Expected: PASS

### Task 2: Refactor BaseAgent into explicit pipeline stages

**Files:**
- Modify: `agents/core/base.py`
- Test: `test/agents/test_agent_pipeline.py`
- Test: `test/agents/test_multimodal_agent_payloads.py`

**Step 1: Write the failing test**

Add tests for:
- `BaseAgent` storing `last_pipeline_trace`
- router stage metadata being recorded
- fallback response staying user-safe on execution failures

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\\agents\\test_agent_pipeline.py test\\agents\\test_multimodal_agent_payloads.py -q`
Expected: FAIL because the trace and safe fallback behavior are missing.

**Step 3: Write minimal implementation**

Split `process` and `process_stream` into helpers:
- request preparation
- route + dispatch plan
- execution
- finalize

Add `last_pipeline_trace` and update it through the turn lifecycle.

Replace raw `Error: ...` final user messages with a safer fallback string that preserves operational meaning without dumping raw exception text.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\\agents\\test_agent_pipeline.py test\\agents\\test_multimodal_agent_payloads.py -q`
Expected: PASS

### Task 3: Improve tool and stream fallback behavior

**Files:**
- Modify: `agents/core/base.py`
- Test: `test/agents/test_agent_fallbacks.py`

**Step 1: Write the failing test**

Add tests for:
- tool execution failures marking pipeline trace degradation
- streaming failures returning a safe `done` state with pipeline metadata

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\\agents\\test_agent_fallbacks.py -q`
Expected: FAIL because the fallback trace and safe error behavior are incomplete.

**Step 3: Write minimal implementation**

Track:
- tool failure count
- fallback mode
- degraded execution stages

Make sure stream failures still expose intent + pipeline metadata for frontend recovery.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\\agents\\test_agent_fallbacks.py -q`
Expected: PASS

### Task 4: Expose pipeline trace through API

**Files:**
- Modify: `api/models.py`
- Modify: `api/routes.py`
- Test: `test/api/test_agent_multimodal_routes.py`
- Test: `test/api/test_agent_stream_routes.py`

**Step 1: Write the failing test**

Add assertions that:
- `POST /api/agent/chat` returns `agent_pipeline`
- streaming `done` payload returns `agent_pipeline`

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\\api\\test_agent_multimodal_routes.py test\\api\\test_agent_stream_routes.py -q`
Expected: FAIL because the field is not returned yet.

**Step 3: Write minimal implementation**

Add additive response fields and serializers only; do not break existing response keys.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\\api\\test_agent_multimodal_routes.py test\\api\\test_agent_stream_routes.py -q`
Expected: PASS

### Task 5: Add regression coverage for routing-to-dispatch mapping

**Files:**
- Create: `test/agents/test_agent_regression_suite.py`
- Optional create: `test/agents/fixtures/agent_regression_cases.json`

**Step 1: Write the failing test**

Create a compact regression suite covering representative intents:
- market analysis
- execution
- portfolio
- memory
- education/research

Check:
- parsed intent
- dispatch target
- expected tool groups
- clarify behavior

**Step 2: Run test to verify it fails**

Run: `python -m pytest test\\agents\\test_agent_regression_suite.py -q`
Expected: FAIL until dispatch planning is wired.

**Step 3: Write minimal implementation**

Wire the regression suite to the new pipeline helpers and keep it deterministic.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test\\agents\\test_agent_regression_suite.py -q`
Expected: PASS

### Task 6: Update Mintlify docs

**Files:**
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/features/agent/index.mdx`

**Step 1: Update docs**

Document:
- new entrypoint pipeline
- router-to-dispatch behavior
- future specialist-agent readiness without claiming specialists already exist
- fallback and recovery behavior

**Step 2: Sanity check navigation**

Open or read the edited files to confirm the new pipeline description is readable.

### Task 7: Run focused verification

**Files:**
- Modify: none

**Step 1: Run focused agent and API tests**

Run:
`python -m pytest test\\agents\\test_agent_pipeline.py test\\agents\\test_agent_fallbacks.py test\\agents\\test_agent_regression_suite.py test\\agents\\test_multimodal_agent_payloads.py test\\api\\test_agent_multimodal_routes.py test\\api\\test_agent_stream_routes.py test\\agents\\test_intent_router.py -q`

Expected: PASS

**Step 2: Commit**

```bash
git add agents/core/pipeline.py agents/core/base.py agents/core/__init__.py api/models.py api/routes.py test/agents/test_agent_pipeline.py test/agents/test_agent_fallbacks.py test/agents/test_agent_regression_suite.py test/agents/test_multimodal_agent_payloads.py test/api/test_agent_multimodal_routes.py test/api/test_agent_stream_routes.py .doch/agents/index.mdx .doch/agents/routing/intent-routing.mdx .doch/features/agent/index.mdx docs/plans/2026-04-19-agent-pipeline-refactor.md
git commit -m "feat: refactor agent entrypoint into traced multi-agent-ready pipeline"
```
