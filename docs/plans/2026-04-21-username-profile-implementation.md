# Username Profile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add editable per-user usernames to Rabit backend with persistent JSON storage.

**Architecture:** Keep wallet auth as the stable identity layer and add a separate backend profile store keyed by `user_id`. Username stays mutable in backend storage, while JWT claims remain unchanged so login tokens do not become stale when the user renames themselves. The auth profile endpoint reads the profile store on demand and the update endpoint writes through the same service.

**Tech Stack:** Python, FastAPI, Pydantic, JSON-backed storage, pytest.

---

### Task 1: Add user profile storage

**Files:**
- Create: `agents/user_profiles/__init__.py`
- Create: `agents/user_profiles/database.py`
- Create: `agents/user_profiles/service.py`
- Modify: `config/settings.py`
- Create: `data/user_profiles.json`

**Step 1: Write the failing test**

Add a service test that creates a username, reloads storage, and verifies the username persists for the same `user_id`.

**Step 2: Run test to verify it fails**

Run: `python -m pytest test/agents/test_user_profiles.py -q`

Expected: FAIL because the storage module does not exist yet.

**Step 3: Write minimal implementation**

Implement JSON-backed storage keyed by `user_id`, plus username validation and update helpers.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test/agents/test_user_profiles.py -q`

Expected: PASS

### Task 2: Expose username through auth API

**Files:**
- Modify: `api/models.py`
- Modify: `api/routes.py`
- Test: `test/api/test_wallet_auth_routes.py`
- Create: `test/api/test_user_profile_routes.py`

**Step 1: Write the failing test**

Add tests that assert:
- `GET /api/auth/me` includes `username`
- `PATCH /api/auth/me/username` updates the stored username

**Step 2: Run test to verify it fails**

Run: `python -m pytest test/api/test_wallet_auth_routes.py test/api/test_user_profile_routes.py -q`

Expected: FAIL because username is not exposed yet.

**Step 3: Write minimal implementation**

Add the new request model, extend `AuthMeResponse`, read from the profile store in `GET /api/auth/me`, and add an authenticated username update route.

**Step 4: Run test to verify it passes**

Run: `python -m pytest test/api/test_wallet_auth_routes.py test/api/test_user_profile_routes.py -q`

Expected: PASS

### Task 3: Final verification

**Files:**
- Modify: none

**Step 1: Run targeted tests**

Run: `python -m pytest test/agents/test_user_profiles.py test/api/test_wallet_auth_routes.py test/api/test_user_profile_routes.py -q`

Expected: PASS
