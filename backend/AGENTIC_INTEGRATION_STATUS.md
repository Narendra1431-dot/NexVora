# NexVora advanced agentic integration

Updated 2026-10-09 (Asia/Calcutta). Core governed workflow is runtime verified; the complete requested advanced platform is NOT yet complete.

## Integration map

- REUSE: NexVora authentication, MongoDB student truth, deterministic domain services, RAG, Redis/ARQ, existing specialist modules.
- ADAPT: Open Dots action gateway, approval lifecycle, audit and confined workspace concepts. MIT attribution retained in app/runtime/OPEN_DOTS_LICENSE.txt.
- REPLACE: standalone runtime persistence with student-scoped Mongo runtime records; owner-token authentication with existing NexVora authentication.
- IGNORE: standalone Open Dots dashboard, sidebar, user database and competing domain state. No Meta provider.
- Agent Zero: separate optional API adapter only; no host terminal/computer execution enabled.

## Implemented and verified

| Area | Implementation | Evidence / limits |
|---|---|---|
| Supervisor | Structured model plan, allowlisted specialists, enforced DAG dependencies, batches up to four | Live 11-specialist run completed; specialist modules call real domain tools, not independent LLMs for every node |
| Jobs | Existing Redis/ARQ worker executes agent_workflow | Live worker completion; FastAPI does not run heavy workflow inline |
| Proof | Mongo runs, steps, tool calls, events, artifacts; actual timestamps and durations | Live records and replayable authenticated SSE; no private reasoning exposed |
| UI | Native Agent Hub, histories, dependency cards, details, cancellation/retry, approvals and audit | Desktop 1280x900 and mobile 390x844 checked; refreshed selected run and artifact retained |
| Approvals | Existing atomic runtimeActions approval records, run-linked audit | Reject/replay/tenant checks in tests; real demo report approved and downloaded through UI |
| Reports | Approval-gated Markdown report saved in confined student workspace | Persisted artifact, authenticated download; student state version unchanged |
| RAG | Existing owned Chroma retrieval plus curated sources | Live cited workflow; owned retrieval scoped by authenticated student |
| Model routing | OpenRouter primary; configured Groq fallback; actual provider usage recorded | OpenRouter HTTP 401. Groq openai/gpt-oss-120b succeeded. This is NOT Llama |
| Runtime health | Reports actual configured/service state | Mongo, worker, vector DB, RAG, approvals and audit healthy; centralBrain degraded_non_llama_fallback |
| Agent Zero | Typed external API client, URL allowlist, output validation, safe status, disabled by default | Contract/security tests only. No live isolated runtime configured |

Existing scores, readiness, rank, assessment results and certificate eligibility remain owned by deterministic NexVora services. Analysis does not directly mutate these values.

## Latest live proof

Run `agt-87a8d444fc2bbb79a958feaa` completed using actual Redis, Mongo, tools and provider calls, without test doubles. Duration 8265 ms; 11 completed specialists, 11 tool calls, one retrieved source, state version 3 to 3. Actual provider: Groq openai/gpt-oss-120b; planning 522 tokens, synthesis 4447 tokens. OpenRouter 401 fallback attempts are recorded. SSE replay verified. Safe evidence: tmp/agent-graph-live-proof.json.

Earlier persisted run `agt-86907611f14498b99ea559a5` was used for the browser approval test: report proposal paused for approval, approval generated an artifact, UI refreshed to 12 tool calls / one approval, and Download saved a real Markdown report. Refresh retained the artifact. Failed historical workflows remain visible; they were not relabeled successful.

## Fixes found during verification

- Returning from Approvals refreshes the selected run and new artifacts.
- Selected run ID is retained in the URL across view changes and refresh.
- Escape closes the step inspector.
- SSE history replay previously fetched details once per event and could hit rate limits. Refreshes are now coalesced and throttled; an 80-event replay regression verifies bounded requests.
- Long download labels wrap within mobile cards; measured document width equals viewport width.
- Successful graph model calls populate provider traces so health reflects the actual fallback.
- Governed action execution has a 60-second timeout. An uncertain failed write is not automatically replayed; its approval remains consumed.

## Validation

- Backend: 11 targeted tests passed (graph, governed runtime, Copilot, intelligence). Covers owned runs/events/artifacts, approval rejection/replay, queue cancellation, retry, provider failure, workspace confinement and Agent Zero contract validation.
- Frontend: Agent Hub regression passed after final changes; earlier governance/mentor component tests and sidebar navigation regression passed.
- TypeScript: npm run lint passed.
- Production: npm run build passed; existing Monaco/ELK large-chunk warnings remain.
- Browser: real demo authentication, persisted execution, report approval/download, refresh, inspector/Escape, desktop/mobile checked. No new console errors after clean reload. Earlier stale Vite hot-reload errors disappeared after reload.
- This is targeted validation, not a claim that every existing feature and every requested advanced workflow has been fully retested.

## Remaining work / blockers

1. OpenRouter/Llama needs valid private OPENROUTER_API_KEY and an accessible configured model. No replacement credentials can be invented.
2. Agent Zero needs an isolated service or Docker deployment. Docker is unavailable and AGENT_ZERO_BASE_URL/API key are not configured. Its adapter is not wired as an executable gateway tool until isolation is verified. Enabling a flag alone does not prove isolation.
3. Advanced Agent Zero browser/research/document/terminal workflows and their end-to-end approval/cancellation tests remain pending. Student code must continue using its dedicated sandbox, never this general runtime.
4. Full requested specialist coverage for research/document generation and all mutation instrumentation remains pending; current tested graph is the career/profile/resume planning flow.
5. Rich PDF/DOCX agent reports, advanced audit filtering, all requested aggregate metrics, and fuller graph-edge visualization remain enhancements beyond the current verified core.
6. Model output remains advisory and can phrase recommendations imprecisely. Deterministic fields remain authoritative; generation does not award mastery for completing a suggested activity.

## Main implementation files

Backend: app/agents/graph.py, app/agents/proof.py, app/agents/supervisor.py, app/tools/registry.py, app/runtime/gateway.py, app/routers/agent_runs.py, app/integrations/agent_zero/*, app/workers/tasks.py, app/brain/schemas.py, app/routers/intelligence.py, app/db.py, app/main.py, app/tests/test_agent_graph.py.

Frontend: src/components/intelligence/AgentHub.tsx and its test, src/components/mentor/AiMentor.tsx, src/types/index.ts, plus minimal App/sidebar/navigation/app-state integration. Existing login and domain pages were retained.

## Local operation

From backend run `./start-agentic-local.ps1`. It starts existing local Redis, Chroma, API, worker and Vite as hidden processes, retaining already listening ports. It installs nothing and does not stop other applications. Use -SkipLocalRedis for an externally configured Redis service. Check actual readiness after startup at http://127.0.0.1:8001/api/v1/health/agentic. App: http://localhost:3000/agent-hub. Logs: backend/tmp/*live*.log.

Agent Zero contract reference: https://github.com/agent0ai/agent-zero/blob/main/docs/developer/connectivity.md and official api_message.py, api_log_get.py, api_terminate_chat.py (inspected 2026-10-07). api_message waits for a result; raw logs may contain private reasoning and are never forwarded to the UI. No claim of a hardened sandbox or successful Agent Zero deployment is made.
