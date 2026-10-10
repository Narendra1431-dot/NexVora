# Quick Fix for Route Duplication Issue

## Problem
The agent-runs routes have double "runs" prefix:
- Expected: `/api/v1/agent/runs/{run_id}`
- Actual: `/api/v1/agent/runs/runs/{run_id}`

## Solution
Change the router prefix in `agent_runs.py` from `/agent/runs` to `/agent/run` (singular)

## Changes Needed

### In `backend/app/routers/agent_runs.py`:

**Line 11 - Change router prefix:**
```python
# BEFORE:
router=APIRouter(prefix='/agent/runs',tags=['agent-execution-proof'])

# AFTER:
router=APIRouter(prefix='/agent/run',tags=['agent-execution-proof'])
```

**Then all routes will become correct:**
- `/api/v1/agent/runs/tools` ✅ (unchanged)
- `/api/v1/agent/run/runs` ❌ (should be `/api/v1/agent/run`)

**Wait, need to fix the route paths too. Let me provide the complete fix.**

### Complete Fix Required:

**Option 1: Fix router prefix AND route paths** (Recommended)

**In `agent_runs.py`:**

```python
# Line 11 - Fix router prefix
router=APIRouter(prefix='/agent/run',tags=['agent-execution-proof'])

# Line 13 - Keep this as-is (since it's under /agent/run prefix)
@router.get('/tools')

# Lines 29-40 - Fix all route paths to remove redundant "runs"
@router.post('/run',status_code=202)        # Changed from '/runs'
async def create_run(payload:graph.StartRun,student_id:str=StudentId):return await graph.create(payload,student_id)

@router.get('/run')                          # Changed from '/runs'
async def list_runs(student_id:str=StudentId):
    rows=[graph.public(r) async for r in col('agent_runs').find({'studentId':student_id,'kind':'execution_graph'}).sort('createdAt',-1).limit(50)]
    return rows

@router.get('/run/{run_id}')                 # Changed from '/runs/{run_id}'
async def run_detail(run_id:str,student_id:str=StudentId):
    # ... rest of function unchanged
```

**And update all other route paths similarly:**
- `/runs/{run_id}/retry` → `/run/{run_id}/retry`
- `/runs/{run_id}/cancel` → `/run/{run_id}/cancel`
- `/runs/{run_id}/roadmap-proposal` → `/run/{run_id}/roadmap-proposal`
- `/runs/{run_id}/report-proposal` → `/run/{run_id}/report-proposal`
- `/runs/{run_id}/artifacts/{artifact_id}/download` → `/run/{run_id}/artifacts/{artifact_id}/download`
- `/runs/{run_id}/events` → `/run/{run_id}/events`

**Option 2: Keep router prefix as `/agent/runs` but fix route paths** (Alternative)

```python
# Line 11 - Keep as-is
router=APIRouter(prefix='/agent/runs',tags=['agent-execution-proof'])

# Fix all route paths to remove one "runs" from each path
@router.post('/run',status_code=202)        # Changed from '/runs'
# ... same as Option 1
```

## Verification

After making the changes, verify that:

1. `curl "http://localhost:8000/api/v1/docs"` shows correct routes
2. `/api/v1/agent/runs/tools` exists ✅ (no change needed)
3. `/api/v1/agent/runs/{run_id}` exists (was `/api/v1/agent/runs/runs/{run_id}`)
4. All other agent-runs routes follow the same pattern

## Summary

**Required change:** Modify `backend/app/routers/agent_runs.py` line 11 and all route paths to remove the duplicate "runs" prefix.

**Impact:** Fixes all agent-runs endpoints to follow correct RESTful patterns.

**Testing:** After fix, run the backend tests to verify all functionality.
