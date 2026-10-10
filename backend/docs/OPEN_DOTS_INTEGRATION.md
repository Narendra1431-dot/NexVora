# Open Dots → NexVora integration map

Source: user-supplied open-dots-main.zip; MIT copyright 2026 Anil-matcha. Inventory with per-file hashes: ../tmp/open-dots-audit/inventory.json. No source setup scripts were executed.

| Component | Decision | Integration |
|---|---|---|
| action_gateway | ADAPT | deny-by-default registry, immutable invocation, consume-before-execute; student-scoped Mongo CAS replaces process dictionaries |
| approval_broker | ADAPT | Mongo pending/decision/expiry, JWT ownership, no HTTP request waiting on a Future |
| workspace_service | ADAPT | separate hashed student directories, restricted file types, no secrets/traversal/junctions, approval before writes |
| provider_service | ADAPT | retain NexVora OpenAI-compatible adapter, configure OpenRouter first; preserve roles, no history promoted to system instructions |
| storage_service / database | REPLACE | existing Mongo; no SQLite or competing profile state |
| secret_store | ADAPT CONCEPT | server-only environment credentials; future connector ciphertext requires external encryption key; no browser key editor |
| connector_actions / search_actions | ADAPT BOUNDARY | typed allowlist, disabled unconfigured integrations; retain NexVora resource search |
| computer_provider / docker_computer_provider | OPTIONAL / DISABLED | no direct host/browser/shell actions; source runtime is prototype, no default enablement |
| chat / approvals / audit routers | ADAPT | existing NexVora JWT, owned sessions and public action metadata only |
| models router | REPLACE | configured server model, no unverified model catalog |
| connectors / computers routers | IGNORE STANDALONE ROUTES | only explicit capability status until deployment exists |
| ApprovalCard / AuditPanel | ADAPT UX | NexVora-native compact components in mentor |
| ComputerPanel / ModelPicker | IGNORE FOR NOW | no fake runtime or provider availability |
| standalone dashboard, sidebar, bots, auth | IGNORE | preserve NexVora UI/auth/domain services |

Findings: original approvals and execution locks are local-process state; unsuitable for NexVora multi-user restart durability. Original workspace accepts more filenames than NexVora should and lacks a secret-file denylist. Docker launcher has resource limits, read-only root, dropped capabilities and no-new-privileges, but its general terminal/network capability is not a student code sandbox. Its connectors depend on external Composio access. Source provider's prompt endpoint is not directly OpenRouter-compatible; reuse the existing bearer/chat-completions adapter.

No Meta or Ollama is active in the new provider routing. OpenRouter access, live queue and optional external integrations must be reported by actual health, never assumed healthy.

## Verified runtime — 7 October 2026

The core governed runtime is integrated, but the complete requested OpenRouter/Llama deployment is **not complete**. OpenRouter returns HTTP 401 with the configured credential. Groq is the working explicit fallback (`openai/gpt-oss-120b`, not a Llama model). No Meta or Ollama adapter is active.

Actual HTTP verification, recorded in `../tmp/agentic-live-verification.json`:

- Original test document uploaded through the authenticated API.
- Redis/ARQ job `job-c6c47c3c47f81e4980c08105` completed at 100%.
- The API retrieved the same document indexed by the separate worker process.
- Grounded answer returned HTTP 200 through Groq, with one validated quotation and the matching uploaded source.
- MongoDB, worker, RAG, supervisor, action gateway, approval broker and audit health passed. OpenRouter remained unavailable; computer runtime and Meta remained disabled.

The API and worker now use a shared Chroma HTTP server. Separate embedded clients against one disk index caused a cross-process retrieval failure; embedded mode remains available for isolated tests. Grounded prompts include only the required learning context and sources. Evidence IDs and document chunk IDs are explicitly distinguished, and provenance validation rejects references that were not supplied to the model. Invalid output is repaired once, then fails closed.

The demo account's approved roadmap export was persisted as a confined workspace artifact. Its audit history survives restart and is visible in the existing Copilot page. Browser inspection on 7 October found no console errors. Screenshot: `../tmp/agentic-copilot-verified.png`.

Validation: 9 backend integration tests passed; 4 Copilot/approval frontend tests passed; sidebar navigation/remount test passed (one separate opt-in live test skipped). The navigation test initially exceeded its lazy-import timeout on a cold parallel run, then passed independently; this timing sensitivity remains. TypeScript checking and production build passed. Existing large Monaco/ELK chunk warnings remain.

## Local service startup

Run from the backend directory. Keep these services on loopback; this is a development setup, not a hardened deployment. MongoDB must already be available using the private backend environment configuration.

Redis was installed from official Ubuntu packages without administrator access into the current WSL user's local directory. Start the existing installation with:

```powershell
wsl.exe -d Ubuntu -- sh -lc 'LD_LIBRARY_PATH=/home/chandu/.local/share/nexvora-redis/root/usr/lib/x86_64-linux-gnu /home/chandu/.local/share/nexvora-redis/root/usr/bin/redis-server --bind 127.0.0.1 --port 6387 --protected-mode yes --daemonize yes --appendonly yes --maxmemory 256mb --maxmemory-policy noeviction --dir /home/chandu/.local/share/nexvora-redis/data --pidfile /home/chandu/.local/share/nexvora-redis/redis.pid --logfile /home/chandu/.local/share/nexvora-redis/redis.log'
```

Run each following long-running command in a separate terminal:

```powershell
.venv\Scripts\chroma.exe run --path data/chroma --host 127.0.0.1 --port 8003
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
.venv\Scripts\python.exe -m app.workers.tasks
npm.cmd --prefix .. run dev -- --port 3000 --host 127.0.0.1
```

Private backend configuration uses `REDIS_URL=redis://127.0.0.1:6387/0`, `CHROMA_HOST=127.0.0.1`, `CHROMA_PORT=8003`. Root `.env.local` sets `NEXVORA_API_TARGET=http://127.0.0.1:8001`. Port 8000 was occupied by another project and was left untouched. Do not start duplicate processes when these ports are already listening.

Check `http://127.0.0.1:8001/api/v1/health/agentic`. To repeat the real ingestion/provider probe, run `.venv\Scripts\python.exe tmp/verify_live_runtime.py`. It creates a clearly named QA account and original sample document; it does not edit existing student records. Provider success depends on valid credentials and current service limits. It never prints credentials.

## Boundaries and remaining scope

- Existing deterministic intent routing and domain agents are retained. This is not unrestricted LLM-generated plan execution.
- Mongo stores owned runtime actions and audit records, not a competing student profile. Student identity comes from NexVora authentication, never model arguments.
- Approved domain mutations call the existing deterministic services. Reject prevents dispatch; stale versions and repeated decisions are rejected. An action interrupted after entering `executing` is not automatically retried: inspect its result before recovery to avoid duplicate side effects.
- Workspace adapters cover notes, roadmap JSON and reviewed resume PDF. Certificate/project-report workspace adapters are not implemented.
- Coding progress is readable through the gateway; arbitrary code review/execution is not a new runtime tool. Existing Coding Space sandbox boundaries remain.
- Connector integrations are disabled until an actual supported adapter and credentials are configured. Encrypted connector-token storage is not implemented; current provider secrets remain server-side environment values with runtime redaction.
- Computer runtime is optional and disabled, with no host shell/browser executor. No claim of a hardened computer sandbox is made.
- Existing ARQ job types are reused. Dedicated new `report_generation` and `resource_validation` jobs are not implemented.
- Source inventory covers the archive and the integration-relevant code was inspected. This is not a formal whole-source security audit.

Preserve the MIT notice in `app/runtime/OPEN_DOTS_LICENSE.txt` when distributing the adapted code.
