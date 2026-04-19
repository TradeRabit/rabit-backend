# Pipeline Quality Pass Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Strengthen the active agent pipeline so response composition, risk framing, and regression coverage are production-ready before the next feature phase.

**Architecture:** Keep the existing composable node graph and improve the quality of the existing nodes instead of introducing new orchestration layers. Upgrade `response_composer` and `risk_review` to produce richer backend-trusted observations, then extend regression tests and docs so the new behavior is locked in.

**Tech Stack:** Python, pytest, Pydantic models, FastAPI docs/OpenAPI, Mintlify `.doch`

---

### Task 1: Upgrade `response_composer`

**Files:**
- Modify: `agents/nodes/response_composer.py`
- Test: `test/agents/test_response_composer_node.py`

**Step 1: Write the failing test**

Add assertions for:
- evidence priority buckets
- conflict detection
- degraded upstream summary
- recommended answer posture

**Step 2: Run test to verify it fails**

Run: `python -m pytest test/agents/test_response_composer_node.py -q`
Expected: FAIL on missing metadata fields.

**Step 3: Write minimal implementation**

Implement a richer summary payload that:
- classifies upstream nodes by evidence strength
- detects degraded upstream nodes
- detects chart/news/execution conflicts
- derives an answer posture for the final runtime

**Step 4: Run test to verify it passes**

Run: `python -m pytest test/agents/test_response_composer_node.py -q`
Expected: PASS

### Task 2: Upgrade `risk_review`

**Files:**
- Modify: `agents/nodes/risk_review.py`
- Test: `test/agents/test_risk_review_node.py`

**Step 1: Write the failing test**

Add assertions for:
- invalidation quality
- confluence strength
- fresh-news fragility
- execution gating impact
- normalized caution reasoning

**Step 2: Run test to verify it fails**

Run: `python -m pytest test/agents/test_risk_review_node.py -q`
Expected: FAIL on missing metadata fields.

**Step 3: Write minimal implementation**

Implement richer risk derivation using existing observations only.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test/agents/test_risk_review_node.py -q`
Expected: PASS

### Task 3: Expand regression parity

**Files:**
- Modify: `test/agents/test_agent_regression_suite.py`
- Modify: `test/agents/test_agent_pipeline.py`
- Modify: `test/agents/test_execution_snapshot_node.py`

**Step 1: Write failing regression tests**

Cover:
- execution degraded matrix
- research ambiguity matrix
- memory ambiguity matrix
- response composer synthesis behavior

**Step 2: Run targeted suite**

Run: `python -m pytest test/agents/test_agent_regression_suite.py test/agents/test_agent_pipeline.py test/agents/test_execution_snapshot_node.py -q`
Expected: FAIL on new expectations.

**Step 3: Adjust code or fixtures minimally**

Keep planner/node behavior stable while making tests reflect the intended contract.

**Step 4: Re-run targeted suite**

Run: same command
Expected: PASS

### Task 4: Sync docs

**Files:**
- Modify: `.doch/features/agent/index.mdx`
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/tools/overview.mdx`

**Step 1: Update diagrams and tables**

Show richer response synthesis and risk framing in the pipeline visuals.

**Step 2: Validate docs references**

Run quick local checks by reading the modified files and ensuring navigation targets still exist.

### Task 5: Run verification

**Files:**
- Test: `test/agents/test_response_composer_node.py`
- Test: `test/agents/test_risk_review_node.py`
- Test: `test/agents/test_agent_regression_suite.py`
- Test: `test/agents/test_agent_pipeline.py`
- Test: `test/agents/test_execution_snapshot_node.py`

**Step 1: Run focused verification**

Run:
`python -m pytest test/agents/test_response_composer_node.py test/agents/test_risk_review_node.py test/agents/test_agent_regression_suite.py test/agents/test_agent_pipeline.py test/agents/test_execution_snapshot_node.py -q`

Expected: PASS
