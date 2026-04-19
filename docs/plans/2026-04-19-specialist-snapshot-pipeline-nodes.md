# Specialist Snapshot Pipeline Nodes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fill the remaining specialist-target gaps by adding `portfolio_snapshot`, `execution_snapshot`, and `memory_snapshot` pipeline nodes.

**Architecture:** Keep the single-runtime entrypoint but ensure each major specialist target has a concrete pre-response enrichment step. Each node stays bounded and read-only, gathers only the highest-signal context for its domain, and injects trusted backend observations into the final prompt.

**Tech Stack:** Python, Pydantic, pytest, existing tool registry, Mintlify `.doch`

---

### Task 1: Extend pipeline planning

**Files:**
- Modify: `agents/core/pipeline.py`
- Test: `test/agents/test_agent_pipeline.py`

Add new node constants and planner rules for:
- `portfolio_specialist`
- `execution_specialist`
- `memory_specialist`

### Task 2: Implement snapshot nodes

**Files:**
- Create: `agents/nodes/portfolio_snapshot.py`
- Create: `agents/nodes/execution_snapshot.py`
- Create: `agents/nodes/memory_snapshot.py`
- Modify: `agents/core/graph_executor.py`
- Modify: `agents/nodes/__init__.py`
- Test: `test/agents/test_portfolio_snapshot_node.py`
- Test: `test/agents/test_execution_snapshot_node.py`
- Test: `test/agents/test_memory_snapshot_node.py`

Add bounded, read-only domain snapshots:
- portfolio balances/collateral/positions
- execution readiness plus open-order state
- memory recall for memory-driven requests

### Task 3: Update docs

**Files:**
- Modify: `.doch/agents/index.mdx`
- Modify: `.doch/agents/routing/intent-routing.mdx`
- Modify: `.doch/features/agent/index.mdx`

Document that the current pipeline now covers market, research, portfolio, execution, and memory-oriented specialist targets with concrete node steps.
