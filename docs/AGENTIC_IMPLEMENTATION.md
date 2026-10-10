# CareerIQ controlled copilot upgrade

Validated October 2, 2026 (local time).

## COMPLETED
- Preserved existing deterministic mastery, confidence, prerequisite, readiness, assessment, project-review and certificate eligibility calculations.
- Added a canonical, student-owned snapshot with state-version checks; strict typed tool/action contracts reject caller-supplied scores and foreign student IDs.
- Added a finite supervisor and 13 domain specialists: Profile, Evidence, Competency, Career, Gap, Roadmap, Resources, Assessment, Projects, Resume, Certificate, RAG and Analytics. They delegate to existing domain services; no arbitrary shell/database tool is exposed.
- Added authenticated `/api/v1/agent/chat`, `/execute`, `/recommendations`, `/activity`, `/history`, plus `/health/agents`.
- Persisted idempotent request runs, conversation history, weekly plans and versioned next-action recommendations in MongoDB. Stable history ordering, stale-answer notices and partial-context metadata are included.
- Added post-commit adaptation for evidence/competency/readiness/roadmap changes. Action logs name tools actually invoked. Certificate recommendations preserve backend eligibility and premium payment gates.
- Integrated existing resource ranking, synthetic evidence/risk advisory models and RAG. Shared RAG indexes public catalog/reference material, never private student documents or answer keys. Generated URLs/citation IDs must exist in supplied context.
- Upgraded Mentor to CareerIQ Agentic Copilot and added compact Dashboard next-action/evidence/activity controls. Action results refresh the workspace; read-only chat refreshes activity. Existing navigation and pages remain intact.
- Retained Groq by explicit user instruction; no silent provider fallback or fabricated provider answers.

## VALIDATION
- Backend full regression suite: **40 passed**. After final adaptation/health edits, all three copilot tests passed again; an additional provider-failure recovery test passed (**41 distinct backend tests verified**).
- TypeScript: `npm run lint` passed.
- Frontend full suite with one worker: **106 passed, 1 optional live test skipped**.
- Explicit live MongoDB navigation run: **2 passed**, including all 11 sidebar pages, Dashboard return and remount, with console-error assertion.
- Production build passed. Existing large ELK bundle warning remains; this upgrade did not add a graph dependency.
- New UI tests verify next-action routing, live values, API error/retry and conversation-driven activity refresh.
- Backend copilot tests cover intent routing, ownership, forbidden tools/score fields, read-only state invariance, persistence, replay protection, stale-action rejection, career changes, resume injection resistance, assessments, certificate eligibility/PDF/evidence, and action preservation when the provider fails.
- Runtime API startup and MongoDB ping succeeded. RAG: 131 documents / 337 chunks, FAISS with local hashing embeddings. Synthetic ML inference passed.
- Real Groq next-action chat succeeded, persisted in MongoDB and returned an identical replay response. A later run confirmed ordered user/assistant history. Subsequent requests hit provider HTTP 429; errors remained explicit, and a requested weekly plan was saved before generation failed. Automated tests verify this recovery path.
- Local development services: frontend http://localhost:3000, API http://127.0.0.1:8000. Runtime samples: `backend/output/qa/copilot-live.json` (synthetic QA account only, no credentials).

## IN PROGRESS
- None actively running.

## PENDING
- Browser/mobile visual inspection. Component/navigation testing is not a substitute for real-browser visual QA.
- A calibrated progress/outcome forecasting model requires real longitudinal training/evaluation data. Existing ML models are explicitly synthetic advisory demonstrations; Analytics reports the forecast as unavailable rather than inventing future readiness.
- Sustained live multi-turn Groq validation after provider quota permits. Read-only and mutation workflows are covered by controlled-provider integration tests, but not every intent has a successful live-provider response.

## BLOCKED
- OpenRouter rejects its configured credential with HTTP 401. User chose to retain Groq.
- Groq intermittently rejects successive requests with HTTP 429. The app reports the provider failure and retains completed domain actions; it does not fabricate a replacement answer.
- Interactive localhost browser QA was denied by the browser access policy. No alternate browser-control workaround was attempted.

## FAILED TESTS
- No remaining automated assertion failures after retesting.
- Initial parallel frontend run timed out waiting for cold lazy imports; the complete single-worker run and explicit live navigation run both passed without changing timeout assertions.
- Live three-prompt Groq smoke script is **not fully passing** because requests after the first successful answer encounter HTTP 429. See runtime sample for exact statuses. This is not claimed as full live-demo completion.

## Architecture and operating limits
- `app/agents`: typed contracts, owned snapshot, finite supervisor, explicit action executor, specialists.
- `app/tools/registry.py`: read-only allowlisted adapters. Only `execute_action` dispatches permitted domain mutations.
- `app/intelligence/recommendations.py`: current mission, evidence and prerequisite projections; weekly time allocation. No mastery inflation or guaranteed readiness gain.
- `app/workflows/adaptation.py`: deterministic post-commit recommendations and activity. Reads can recover a failed recommendation publication.
- `src/components/common/CareerIntelligencePanel.tsx`: shared dashboard/activity presentation.
- Successful requests replay by student/request ID; reuse for another payload and replay of running/failed requests return 409. This does not claim global serialization of all legacy app mutations.
- LLM responses are advisory. Only explicit supported actions invoke domain services. Certificates and reviewer decisions remain outside conversational privilege.
