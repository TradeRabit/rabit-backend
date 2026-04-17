# Mem0 Agent Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Repair Mem0 self-hosted integration, expose backend memory management APIs, and connect user memory to the Rabit agent flow with memory tools.

**Architecture:** Update the Mem0 client to match the OSS REST API, route backend calls through a single client abstraction, and inject user-scoped memory context into agent requests when `user_id` is present. Add dedicated backend endpoints for UI memory management and register Mem0 tools so the agent can read and manage long-term memory intentionally.

**Tech Stack:** FastAPI, aiohttp, Anthropic SDK, Docker Compose, pytest

---

### Task 1: Repair Mem0 client + runtime configuration

**Files:**
- Modify: `agents/memory/mem0_client.py`
- Modify: `config/settings.py`
- Modify: `.env.example`
- Modify: `docker-compose.yml`

### Task 2: Add agent memory context + Mem0 tools

**Files:**
- Modify: `agents/core/base.py`
- Modify: `agents/core/trading_agent.py`
- Create: `agents/tools/mem0_tools.py`
- Modify: `agents/tools_registry/register_tools.py`

### Task 3: Add backend memory management API

**Files:**
- Modify: `api/models.py`
- Modify: `api/routes.py`

### Task 4: Add tests and verification

**Files:**
- Create: `test/agents/test_mem0_client.py`
- Create: `test/agents/test_mem0_tools.py`
- Create: `test/api/test_memory_routes.py`
- Modify: `test/agents/test_multimodal_agent_payloads.py`
