# Pipeline Gap Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the main structural gaps in the current agent pipeline before moving on to chart-writing workflows.

**Architecture:** Keep the current router-ready single-runtime architecture, but make the pipeline more honest and complete by turning `response_composer` into a real node, adding concrete `clarification` and `general fallback` paths, updating `next_agent_status` from actual execution, and extending BaseAgent integration coverage beyond the chart path.

**Tech Stack:** Python, Pydantic, pytest, existing pipeline executor, Mintlify `.doch`

---

### Task 1: Add the missing general and clarification nodes

**Files:**
- Modify: `agents/core/pipeline.py`
- Modify: `agents/core/graph_executor.py`
- Create: `agents/nodes/clarification_prep.py`
- Create: `agents/nodes/general_fallback.py`

Add concrete pipeline nodes so low-confidence and clarification-required requests no longer stop at a planned target with no runtime node.

### Task 2: Make `response_composer` a real node

**Files:**
- Create: `agents/nodes/response_composer.py`
- Modify: `agents/nodes/__init__.py`
- Modify: `agents/core/graph_executor.py`

Implement a composable node that summarizes prior node observations into a trusted composition block before the final runtime answer.

### Task 3: Make trace semantics reflect actual execution

**Files:**
- Modify: `agents/core/base.py`
- Modify: `agents/core/pipeline.py`

Update `next_agent_status` based on executed nodes so the trace can distinguish:
- planned only
- represented by pipeline nodes
- clarification node completed
- general fallback node completed
- degraded path

### Task 4: Add integration parity tests

**Files:**
- Modify: `test/agents/test_agent_pipeline.py`

Add BaseAgent integration tests for:
- portfolio path
- execution path
- memory path
- clarification path
- general fallback path

### Task 5: Update docs

**Files:**
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/features/agent/index.mdx`

Document that the pipeline now covers:
- market
- research
- portfolio
- execution
- memory
- general fallback
- clarification
- response composition
