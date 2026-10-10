> Superseded provider policy: the Open Dots integration removes Meta from active routing. See docs/OPEN_DOTS_INTEGRATION.md. Historical validation notes below describe the earlier integration.

# NexVora intelligence integration

## Current status (5 October 2026)

The integration is implemented, but the requested live Meta/Llama and Redis deployment is **not complete**. MongoDB and Chroma are healthy. Live structured reasoning succeeds through Groq `openai/gpt-oss-120b`; this is explicitly reported as `degraded_non_llama_fallback`, not Llama. Meta has no API credential, OpenRouter returns HTTP 401, and the available Groq account has no tested generative Llama model. No Redis server, Docker runtime, or installed WSL distribution is available on this machine. Do not interpret queue unit/integration tests as a successful live Redis deployment.

## Data flow and boundaries

Authenticated upload → Mongo durable outbox → Redis/ARQ worker → extraction → provenance chunks → local MiniLM embeddings → Chroma → hybrid retrieval → structured provider response → citation validation → Mongo result → background activity UI.

Canonical student state comes from the existing domain services. AI outputs are advisory. Mastery, readiness, assessment scores, XP, rank, evidence verification and certificate eligibility remain under existing deterministic authority. Resume claims alone are not verified evidence.

Provider order is configurable, currently Meta → OpenRouter → Groq. Keys remain on the server. Responses carry the actual provider/model; schema failures and invalid citation IDs/quotes fail validation. Citation validation establishes source/quote integrity, not a general proof of semantic entailment. Documents are untrusted input.

## Main files

- `app/providers/`: provider adapters, bounded retries, structured output and fallback.
- `app/brain/`: bounded canonical context and validated advisory orchestration.
- `app/rag/`: PDF/TXT/DOCX extraction, LangChain chunks, MiniLM, Chroma, hybrid retrieval.
- `app/workers/`: JSON-serialized ARQ jobs, Mongo outbox, progress, retry/recovery and per-student serialization.
- `app/routers/intelligence.py`: private documents/jobs/results/brain APIs and service health.
- `../src/components/intelligence/`: background activity and course-material questions, used by Resources and AI Mentor.

Existing AI/RAG, resume and workflow routes are retained for compatibility. `/api/v1/rag/query` accepts the new question/document IDs shape and the legacy message shape. Background resume analysis is used when both queue and worker are healthy; otherwise the existing direct resume parser remains usable.

## Runtime configuration

Nonsecret defaults are configured in `.env`. Add account credentials privately; never commit them.

| Setting | Purpose |
| --- | --- |
| `REDIS_URL` | Redis connection; local default `redis://127.0.0.1:6379/0` |
| `META_API_KEY` or `MODEL_API_KEY` | Authorized Meta API credential |
| `META_BASE_URL`, `META_MODEL` | Current official endpoint and account-accessible model |
| `PRIMARY_LLM_PROVIDER` | Interactive reasoning provider |
| `BACKGROUND_LLM_PROVIDER` | Background provider (defaults to Meta) |
| `FALLBACK_LLM_PROVIDER` | Ordered comma-separated fallback providers |
| `ALLOW_AI_FALLBACK` | Whether fallback is allowed |
| `BRAIN_GROQ_MODEL` | Actual Groq model used by this integration |
| `ENABLE_CENTRAL_BRAIN` | Enables the mentor integration |
| `VECTOR_STORE` | Currently `chroma`; adapter boundary permits a future replacement |
| `ENABLE_DOCUMENT_OCR` | Optional OCR; requires separately installed Tesseract/pytesseract |

When Docker is available, start local Redis from this directory:

```powershell
docker compose -f compose.intelligence.yml up -d
.\start-intelligence-worker.ps1
```

The Compose service binds only to localhost and persists Redis data. The worker launcher checks Redis before starting a hidden worker. Alternatively configure an existing private Redis service. Do not expose an unauthenticated Redis instance publicly. Restart the API and worker after changing provider configuration.

Check `GET /health/intelligence`: require healthy queue, worker heartbeat, Mongo and vector store before declaring asynchronous deployment ready. Live Meta and a usable generative Llama model still require authorized account access. The current Meta model configuration is not represented as Llama.

## Jobs and storage

Twelve typed jobs cover ingestion/indexing, resume analysis/generation, career explanations, roadmap proposals, resource enrichment, assessment proposals, project recommendations, certificate descriptions and student refresh. Proposal jobs return advisory material; they do not automatically publish assessments, grant certificates or overwrite the roadmap. Resume generation delegates to the existing validated draft service.

Mongo collection aliases: `intelligence_jobs`, `intelligence_documents`, `intelligence_chunks`, `intelligence_results`, `intelligence_traces` (mapped to physical collection names by `app/db.py`). Student ownership is checked on requests and retrieval. Chroma also filters by student. Progress and results survive page refresh. When Redis is offline, submissions remain Queued with an explicit waiting message. Recovery reconciles the durable outbox. Only queued jobs can be cancelled safely.

Local vector data lives in `data/chroma`. MiniLM downloads on first use; the model was downloaded and real 384-dimensional embeddings were tested. Production currently has zero indexed chunks. Scanned PDFs need optional OCR; failures are explicit rather than fabricated content.

## Validation performed

- 15 backend tests across intelligence, coding, resume flow, domain and graph passed.
- 14 legacy backend regression tests passed with central-brain integration disabled to exercise preserved legacy paths.
- All three intelligence tests passed in the final run, including a new regression check for repairing fabricated citations while preserving deterministic facts.
- 10 focused frontend tests passed; one opt-in live navigation test was skipped.
- TypeScript checking and production build passed. Existing bundle-size warnings remain.
- Real Mongo, Chroma and MiniLM exercised: source pagination, tenant isolation, ingestion, retrieval, resume consistency, cancellation, retry and failures.
- Queue transport/locks and LLM outputs in automated integration tests use explicit doubles. A real Redis/ARQ end-to-end run remains pending.
- Live Groq structured generation and canonical-state reasoning passed; live health reports actual failed/missing providers.

Before production: provision Redis and run queued upload through a real worker; supply Meta/model access and verify it; test grounded generation with real indexed documents and the selected live model; configure OCR if required; harden parser workers and operational resource limits for untrusted production uploads. Resume draft creation is not guaranteed exactly-once across a process crash after creation but before job checkpointing.

Official references: [Meta API overview](https://dev.meta.ai/docs/overview), [ARQ](https://arq-docs.helpmanual.io/), [Chroma](https://docs.trychroma.com/).
