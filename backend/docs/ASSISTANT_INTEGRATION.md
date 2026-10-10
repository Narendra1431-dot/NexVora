# Conversational assistant audit and file plan

2026-10-09. Additive integration; existing domain services remain authoritative.

## Architecture inspected
React 19 / Vite / TypeScript UI: App.tsx lazy-loads pages; AppStateProvider owns authenticated workspace projection, history navigation and mutations. Existing Header/sidebar, EditHistoryProvider and LoginSplash retained. FastAPI 0.115 / Python 3.12 uses JWT StudentId dependency, Mongo collection registry, Pydantic input validation and rate limiting. Vite proxies /api to the configured local API. Redis/ARQ handles heavy intelligence work, Chroma stores owned document vectors. Canonical engine/state + competency derive mastery/readiness from evidence; ranker and advisory models are supportive, not grading authorities. Resume ingestion validates PDF/TXT, extracts sections and known skills, adds unverified claims, recalculates selected-career scoring, and returns live state. Latest resume scopes claim evidence. Uploaded material uses owned Mongo chunks + Chroma and lexical reranking. Existing Copilot routes project intents to specialist tools and gates mutations through approvals. Model adapters route OpenRouter then configured fallback; current working fallback is Groq. Mongo remains canonical; no competing student state.

## Rasa decision
Official RasaHQ/rasa README marks Open Source maintenance mode. Inspected 3.6.x pyproject declares 3.6.21, Apache-2.0 and Python >=3.8,<3.11, with old TensorFlow/Sanic constraints. This is the observed source version, not a promise of commercial support. It must not be installed into this Python 3.12 environment. REST channels, trackers/slots and custom actions could bridge an isolated Rasa service, but duplicate existing routing/memory without providing web search or STT/TTS by themselves. Current CALM/Pro supports LLM flows, custom actions, enterprise-search and voice integrations; it is a separate product/license decision, not the classic Apache repository. Selected architecture: reuse the existing Python/Pydantic conversational runtime plus optional open-source SearXNG HTTP adapter (or Brave Search), browser Web Speech APIs, and current RAG. No Rasa service is installed or falsely labeled active.

## File plan before implementation
Modify only app/main.py (router), app/db.py (assistant message collection/index), src/App.tsx (assistant mount). Add app/assistant/{schemas,research,service}.py, app/routers/assistant.py, src/components/assistant/{AssistantWidget,useVoice}.tsx/ts, focused tests and this report. Leave authentication, grading, evidence, resume parser/scoring, roadmap, certificates, coding runner, existing Copilot and all page layouts unchanged. Reuse StudentId, providers/router, supervisor, snapshot, owned RAG, modal hook and intelligenceApi. New authenticated APIs: POST /api/v1/assistant/chat, GET /assistant/history, GET /assistant/capabilities. No new package dependencies. Optional environment: BRAVE_SEARCH_API_KEY, SEARXNG_URL. No secrets in frontend. Search queries require privacy minimization and are distinct from internal context.

## Official references
- https://github.com/RasaHQ/rasa
- https://raw.githubusercontent.com/RasaHQ/rasa/3.6.x/pyproject.toml
- https://rasa.com/rasa-product-release-and-maintenance-policy
- https://legacy-docs-oss.rasa.com/docs/rasa/connectors/your-own-website/
- https://rasa.com/docs/pro/build/custom-actions/
- https://rasa.com/docs/pro/build/voice-assistants/
- https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition
- https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis
- https://api-dashboard.search.brave.com/app/documentation/web-search/get-started
- https://docs.searxng.org/dev/search_api.html

## Implementation report — 2026-10-09

1. **Existing architecture:** React/Vite, FastAPI/Python 3.12, authenticated Mongo state, Chroma retrieval, Redis/ARQ and governed supervisor, as audited above.
2. **Rasa verification:** Official repository and 3.6.x dependency manifest inspected; Apache classic distribution is distinct from Pro/CALM.
3. **Decision:** Rasa classic rejected for this environment's Python incompatibility and duplicated orchestration. The assistant uses the existing runtime; it is not presented as Rasa-based.
4. **References:** Official repository, Rasa, browser speech and search documentation links are listed above.
5. **Integration:** Authenticated floating assistant → FastAPI facade → bounded canonical state/owned RAG, existing model adapters, optional public search; action requests delegate to the existing governed supervisor.
6. **Modified existing files:** `src/App.tsx`, `backend/app/main.py`, `backend/app/db.py` only for mounting, routing and conversation collection/index registration.
7. **Added files:** `backend/app/assistant/{__init__,schemas,research,service}.py`; `backend/app/routers/assistant.py`; `backend/app/tests/test_assistant.py`; `src/components/assistant/{AssistantWidget.tsx,useVoice.ts,AssistantWidget.test.tsx,useVoice.test.tsx}`; this report.
8. **Untouched domain logic:** Authentication, competency calculations, assessments, resume scoring, certificates, coding sandbox, roadmap and existing page designs.
9. **Dependencies:** No new packages required. Existing httpx, Pydantic, Mongo, React and browser speech APIs are reused.
10. **Environment:** Optional `BRAVE_SEARCH_API_KEY` (selected by user) or `SEARXNG_URL` in backend/.env. Neither was present at the last private presence-only check. No key is fabricated or exposed to the client.
11. **Data:** JWT-derived student ID scopes history and canonical projection. Messages persist in Mongo assistantMessages. Public search cache contains technical queries/results only, not student state.
12. **Chat:** Typed question → project/general/external/mixed routing → structured answer validation → persistent history. Busy/error states retain the draft on failure. Latest answer auto-scrolls into view. Recommendations do not themselves execute actions.
13. **Voice:** Explicit microphone click → browser transcription → editable text → same chat endpoint; explicit speaker click reads the same answer. Unsupported browsers retain text input. Browser speech may use a remote service. Actual microphone/audio quality remains unverified.
14. **RAG:** Existing tenant-owned retrieval supplies up to two bounded excerpts; generated source IDs and exact quotes are checked. Retrieval failure is disclosed. Existing ingestion/vector ownership is unchanged; a new live document-ingestion-to-widget citation test remains pending.
15. **Web search:** Brave/SearXNG adapters use bounded public technical topic queries, HTTPS URL checks and a 15-minute cache. Missing search produces an explicit unavailable response rather than fabricated current facts. Live service verification requires a valid key.
16. **Deep research:** Multiple bounded topic queries, deduplication, limited official-domain page reads, citation checks and real source/domain/page counts. This is a bounded research workflow, not unrestricted browsing. Adapter behavior was tested with HTTP doubles; live multi-source research remains pending.
17. **Security:** Strict schemas reject spoofed student IDs; ownership/auth/idempotency tests pass. No direct grading/state writes by the conversational model. Secrets are rejected/redacted; arbitrary generated URLs and invalid citations are rejected. Prompt injection defenses are layered but not a guarantee of perfect factual grounding. Unsupported action-claim checks are conservative and may request a retry.
18. **Tests:** Focused backend regression run: 15 passed; latest assistant backend rerun: 2 passed. Frontend assistant/voice: 3 passed. TypeScript check passed. Navigation standalone rerun passed (one opt-in live test skipped); a previous concurrent run hit its timeout. Live general explanation and personalized top-three gaps returned successfully using configured fallback. Desktop 1280×900 panel and mobile 390×844 fit were visually checked; history reloaded on reopening. Browser error log was empty. Browser capture briefly timed out, then recovered; viewport override reset. The earlier erroneous test answer remains in demo history; the latest response no longer claims scheduling.
19. **Pending/limitations:** Valid Brave key and live search/deep research; physical voice test; live owned-document citation test. OpenRouter returned 401 earlier; Groq fallback works but has also returned 429 under larger requests. Bounded state reduced prompt size. Search supports the enumerated technical topics, not arbitrary personal web queries. This is not a claim that all requested live capabilities are complete.
20. **Run commands:** From PowerShell:

```powershell
Set-Location 'C:\Users\boddu\Downloads\NSRIT HACKTHON\backend'
.\start-agentic-local.ps1
.\.venv\Scripts\python.exe -m pytest app/tests/test_assistant.py -q
Set-Location '..'
npm run lint
npx vitest run src/components/assistant/AssistantWidget.test.tsx src/components/assistant/useVoice.test.tsx
npm run build
```

Open `http://localhost:3000`. The startup helper uses the existing Mongo configuration, local Redis/Chroma and worker installations. Add a valid private search key and restart the backend before attempting live search validation.
