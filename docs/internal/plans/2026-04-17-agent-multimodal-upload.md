# Agent Multimodal Upload Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a temporary upload pipeline that lets the Rabit agent accept image and PDF inputs and send them to Claude/OpenRouter as multimodal content.

**Architecture:** The backend stores uploads temporarily in local disk storage with a JSON metadata registry. Agent chat requests reference short-lived `file_id` values, which are resolved into internal attachment models and transformed into Anthropic/OpenRouter message blocks before calling the model.

**Tech Stack:** FastAPI, Pydantic, Anthropic SDK, OpenRouter via Anthropic-compatible client, local filesystem temp storage, pytest

---

### Task 1: Add temporary upload domain models and manager

**Files:**
- Create: `agents/uploads/models.py`
- Create: `agents/uploads/manager.py`
- Create: `agents/uploads/__init__.py`
- Test: `test/agents/test_upload_manager.py`

**Step 1: Write failing tests**
- Cover create upload metadata, resolve upload, delete upload, expire upload cleanup.

**Step 2: Run tests to verify failure**

Run: `python -m pytest test/agents/test_upload_manager.py -q`

**Step 3: Write minimal implementation**
- Add upload metadata models
- Add JSON-backed upload registry
- Add filesystem save / resolve / delete / cleanup helpers

**Step 4: Run tests to verify pass**

Run: `python -m pytest test/agents/test_upload_manager.py -q`

**Step 5: Commit**

```bash
git add agents/uploads test/agents/test_upload_manager.py
git commit -m "feat: add temporary upload manager"
```

### Task 2: Upgrade BaseAgent for multimodal content

**Files:**
- Modify: `agents/core/base.py`
- Modify: `agents/memory/conversation.py`
- Modify: `agents/compression/compressor.py`
- Test: `test/agents/test_multimodal_agent_payloads.py`

**Step 1: Write failing tests**
- Verify Anthropic message block generation for image + PDF attachments
- Verify OpenRouter message block generation for image + PDF attachments
- Verify conversation history remains text-compressible

**Step 2: Run tests to verify failure**

Run: `python -m pytest test/agents/test_multimodal_agent_payloads.py -q`

**Step 3: Write minimal implementation**
- Add attachment models / input handling
- Normalize history into text summaries for memory/compression
- Build provider-specific content blocks before `messages.create(...)`

**Step 4: Run tests to verify pass**

Run: `python -m pytest test/agents/test_multimodal_agent_payloads.py -q`

**Step 5: Commit**

```bash
git add agents/core/base.py agents/memory/conversation.py agents/compression/compressor.py test/agents/test_multimodal_agent_payloads.py
git commit -m "feat: add multimodal agent payload support"
```

### Task 3: Add agent upload + chat API endpoints

**Files:**
- Modify: `api/models.py`
- Modify: `api/routes.py`
- Test: `test/api/test_agent_multimodal_routes.py`

**Step 1: Write failing tests**
- Upload returns `file_id`
- Chat accepts `attachments`
- Delete removes upload
- Expired upload is rejected

**Step 2: Run tests to verify failure**

Run: `python -m pytest test/api/test_agent_multimodal_routes.py -q`

**Step 3: Write minimal implementation**
- Add request/response models
- Add `/api/agent/uploads`, `/api/agent/chat`, `/api/agent/uploads/{file_id}`
- Resolve uploaded files into agent attachments

**Step 4: Run tests to verify pass**

Run: `python -m pytest test/api/test_agent_multimodal_routes.py -q`

**Step 5: Commit**

```bash
git add api/models.py api/routes.py test/api/test_agent_multimodal_routes.py
git commit -m "feat: add multimodal agent api routes"
```

### Task 4: Wire configuration and docs

**Files:**
- Modify: `config/settings.py`
- Modify: `.env.example`
- Modify: `agents/README.md`

**Step 1: Add config knobs**
- Upload dir
- TTL
- max size

**Step 2: Document API usage**
- Upload flow
- chat request examples

**Step 3: Run targeted verification**

Run:
```bash
python -m pytest test/agents/test_upload_manager.py test/agents/test_multimodal_agent_payloads.py test/api/test_agent_multimodal_routes.py -q
python -c "import main; print('IMPORT_OK')"
```

**Step 4: Commit**

```bash
git add config/settings.py .env.example agents/README.md
git commit -m "docs: document multimodal upload pipeline"
```
