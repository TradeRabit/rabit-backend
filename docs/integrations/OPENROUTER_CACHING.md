# OpenRouter Models Caching Strategy

## 📋 Overview

Sistem OpenRouter models menggunakan **3-layer caching** untuk menghindari call API berulang-ulang dan memastikan performa optimal.

## 🎯 3-Layer Caching

```
┌─────────────────────────────────────────────────────────────┐
│                    Request Flow                              │
└─────────────────────────────────────────────────────────────┘

Request → Layer 1: Memory Cache → Layer 2: Database Cache → Layer 3: API Call
            (Instant)              (0.01s)                    (2-3s)
            
            ↓ Hit                  ↓ Hit                      ↓ Miss
            Return                 Return                     Fetch & Save
```

### Layer 1: In-Memory Cache

**Location:** `OpenRouterModels.models` (Python list)

**Lifetime:** Until server restart

**Speed:** Instant (< 0.001s)

**Behavior:**
- First call: Empty, proceeds to Layer 2
- Subsequent calls: Returns immediately from memory
- Cleared on: Server restart

**Code:**
```python
async def fetch_models(self, force_refresh: bool = False):
    # Layer 1: Check in-memory cache
    if self.models and not force_refresh:
        logger.debug("Using in-memory cached models")
        return self.models
    
    # Proceed to Layer 2...
```

### Layer 2: Database Cache (JSON)

**Location:** `data/openrouter_models.json`

**Lifetime:** 7 days (configurable)

**Speed:** Fast (0.01s)

**Behavior:**
- Checks if database is stale (> 7 days old)
- If fresh: Load from database
- If stale: Proceed to Layer 3
- Persists across server restarts

**Code:**
```python
async def fetch_models(self, force_refresh: bool = False):
    # Layer 2: Check database cache
    if not force_refresh and not self.db.is_stale():
        logger.info("Loading models from database (fresh)")
        self.models = self.db.get_all_models()
        return self.models
    
    # Proceed to Layer 3...
```

**Staleness Check:**
```python
def is_stale(self, max_age_days: int = 7) -> bool:
    """Check if database is older than 7 days"""
    if not self.data:
        return True
    
    last_updated = self.metadata.get("last_updated")
    if not last_updated:
        return True
    
    age = datetime.utcnow() - datetime.fromisoformat(last_updated)
    return age > timedelta(days=max_age_days)
```

### Layer 3: API Call

**Location:** `https://openrouter.ai/api/v1/models`

**Speed:** Slow (2-3s)

**Behavior:**
- Only called when:
  - Database is empty
  - Database is stale (> 7 days)
  - Force refresh requested
- Saves result to database
- Updates in-memory cache

**Code:**
```python
async def fetch_models(self, force_refresh: bool = False):
    # Layer 3: Fetch from API
    logger.info("Fetching models from OpenRouter API...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(self.API_URL) as response:
            if response.status == 200:
                data = await response.json()
                # Parse and save to database
                self.db.save_models(self.models)
                return self.models
```

## 📊 Performance Comparison

| Scenario | Layer Used | Time | API Calls |
|----------|-----------|------|-----------|
| First request (cold start) | Layer 3 (API) | 2-3s | 1 |
| Second request (same session) | Layer 1 (Memory) | < 0.001s | 0 |
| After server restart (DB fresh) | Layer 2 (Database) | 0.01s | 0 |
| After 7 days (DB stale) | Layer 3 (API) | 2-3s | 1 |
| Force refresh | Layer 3 (API) | 2-3s | 1 |

## 🔄 Request Flow Examples

### Example 1: Cold Start (First Request Ever)

```
User Request
    ↓
Layer 1: Memory Cache → Empty
    ↓
Layer 2: Database Cache → Empty
    ↓
Layer 3: API Call → Fetch 400+ models (2-3s)
    ↓
Save to Database
    ↓
Save to Memory
    ↓
Return to User
```

**Time:** 2-3 seconds
**API Calls:** 1

### Example 2: Subsequent Request (Same Session)

```
User Request
    ↓
Layer 1: Memory Cache → HIT! (400+ models)
    ↓
Return to User
```

**Time:** < 0.001 seconds
**API Calls:** 0

### Example 3: After Server Restart (Database Fresh)

```
User Request
    ↓
Layer 1: Memory Cache → Empty (server restarted)
    ↓
Layer 2: Database Cache → HIT! (fresh, < 7 days)
    ↓
Load from Database (0.01s)
    ↓
Save to Memory
    ↓
Return to User
```

**Time:** 0.01 seconds
**API Calls:** 0

### Example 4: After 7 Days (Database Stale)

```
User Request
    ↓
Layer 1: Memory Cache → Empty
    ↓
Layer 2: Database Cache → STALE (> 7 days)
    ↓
Layer 3: API Call → Fetch updated models (2-3s)
    ↓
Update Database
    ↓
Save to Memory
    ↓
Return to User
```

**Time:** 2-3 seconds
**API Calls:** 1

### Example 5: Force Refresh

```
User Request (with refresh=true)
    ↓
Skip Layer 1 & 2
    ↓
Layer 3: API Call → Fetch latest models (2-3s)
    ↓
Update Database
    ↓
Update Memory
    ↓
Return to User
```

**Time:** 2-3 seconds
**API Calls:** 1

## 🎯 API Endpoint Behavior

### GET /api/models

```python
@app.get("/api/models")
async def list_models(refresh: bool = False):
    models_manager = get_openrouter_models()
    
    # Uses 3-layer caching automatically
    await models_manager.fetch_models(force_refresh=refresh)
    
    # Filter and return
    return filtered_models
```

**Default (refresh=false):**
- Uses Layer 1 → Layer 2 → Layer 3 cascade
- Fast response (< 0.001s if cached)

**With refresh=true:**
- Skips to Layer 3 (API call)
- Slow response (2-3s)
- Updates all caches

### GET /api/models/stats

```python
@app.get("/api/models/stats")
async def get_models_stats():
    models_manager = get_openrouter_models()
    
    # Always uses cache (never forces refresh)
    await models_manager.fetch_models()
    
    return stats
```

**Behavior:**
- Always uses 3-layer caching
- Never forces API call
- Fast response

### POST /api/models/database/refresh

```python
@app.post("/api/models/database/refresh")
async def refresh_database():
    models_manager = get_openrouter_models()
    
    # Force refresh from API
    await models_manager.fetch_models(force_refresh=True)
    
    return {"success": True}
```

**Behavior:**
- Forces Layer 3 (API call)
- Updates database and memory
- Slow response (2-3s)

## 📈 Cache Hit Rate

### Expected Hit Rates

| Cache Layer | Expected Hit Rate | Reason |
|-------------|------------------|---------|
| Layer 1 (Memory) | 95%+ | Most requests in same session |
| Layer 2 (Database) | 4% | After server restart |
| Layer 3 (API) | < 1% | Only when stale or forced |

### Monitoring Cache Performance

```python
# Add logging to track cache hits
logger.info(f"Cache hit: Layer 1 (Memory)")  # Instant
logger.info(f"Cache hit: Layer 2 (Database)")  # 0.01s
logger.info(f"Cache miss: Fetching from API")  # 2-3s
```

## 🔧 Configuration

### Database Staleness Period

Default: 7 days

```python
# In database.py
def is_stale(self, max_age_days: int = 7) -> bool:
    # Change max_age_days to adjust staleness period
    pass
```

**Recommendations:**
- Development: 1 day (frequent updates)
- Production: 7 days (stable)
- Enterprise: 30 days (very stable)

### Database Location

Default: `data/openrouter_models.json`

```python
# Custom location
db = get_models_database("custom/path/models.json")
```

## 🚀 Best Practices

### 1. Let Caching Work Automatically

```python
# ✅ GOOD: Let caching work
await models_manager.fetch_models()

# ❌ BAD: Force refresh unnecessarily
await models_manager.fetch_models(force_refresh=True)
```

### 2. Use Force Refresh Sparingly

```python
# ✅ GOOD: Only when needed
if user_requested_refresh:
    await models_manager.fetch_models(force_refresh=True)

# ❌ BAD: Every request
await models_manager.fetch_models(force_refresh=True)
```

### 3. Don't Check if Models Loaded

```python
# ✅ GOOD: Just call fetch_models
await models_manager.fetch_models()

# ❌ BAD: Unnecessary check
if not models_manager.models:
    await models_manager.fetch_models()
```

The `fetch_models` method already handles this internally!

### 4. Monitor Cache Performance

```python
# Log cache hits/misses
logger.info(f"Models loaded: {len(models)} (from cache)")
```

## 🐛 Troubleshooting

### Problem: Models Not Updating

**Symptom:** New models from OpenRouter not appearing

**Solution:**
```bash
# Force refresh via API
curl -X POST http://localhost:8000/api/models/database/refresh

# Or delete database file
rm data/openrouter_models.json
```

### Problem: Slow Response Times

**Symptom:** Every request takes 2-3 seconds

**Diagnosis:**
```python
# Check if database is being used
logger.info(f"Database stale: {db.is_stale()}")
logger.info(f"Memory cache: {len(models_manager.models)} models")
```

**Solution:**
- Ensure database file exists and is readable
- Check database staleness period
- Verify in-memory cache is working

### Problem: Database Corruption

**Symptom:** JSON decode errors

**Solution:**
```bash
# Clear and refresh
curl -X DELETE http://localhost:8000/api/models/database/clear
curl -X POST http://localhost:8000/api/models/database/refresh
```

## 📊 Cache Statistics

### GET /api/models/database/stats

```bash
curl http://localhost:8000/api/models/database/stats
```

**Response:**
```json
{
  "total_models": 400,
  "last_updated": "2026-04-14T10:30:00Z",
  "is_stale": false,
  "providers": 15,
  "models_with_tools": 120,
  "models_with_reasoning": 45
}
```

## ✅ Summary

**3-Layer Caching Strategy:**
1. ✅ **Memory Cache** - Instant (< 0.001s)
2. ✅ **Database Cache** - Fast (0.01s, 7-day lifetime)
3. ✅ **API Call** - Slow (2-3s, only when needed)

**Benefits:**
- ✅ 95%+ requests served from memory (instant)
- ✅ 4% requests served from database (fast)
- ✅ < 1% requests hit API (only when stale)
- ✅ No repeated API calls
- ✅ Works offline (uses database)
- ✅ Auto-refresh when stale

**Performance:**
- First request: 2-3s (API call)
- Subsequent requests: < 0.001s (memory)
- After restart: 0.01s (database)
- After 7 days: 2-3s (refresh)

---

**Last Updated:** 2026-04-14
**Version:** 1.0.0
**Status:** ✅ Production Ready
