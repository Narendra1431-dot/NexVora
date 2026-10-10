# Personalized Learning & Career Intelligence

React/TypeScript + FastAPI + MongoDB. The frontend reads one server-computed student snapshot. Evidence changes recalculate mastery, confidence, career readiness, resume claim coverage and prerequisite-aware roadmap state. The LLM has no state-writing tools.

## Run on Windows

From the project root:

```powershell
npm.cmd install
npm.cmd run dev
```

From `backend` in a second terminal:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

MongoDB must be running at `mongodb://localhost:27017`; database `career_intelligence`. The local database was verified. If using Docker for a new database: `docker compose up -d mongodb`. Do not start a second MongoDB on an occupied port.

Open http://localhost:3000. Register an account or choose **Explore seeded demo**. The demo persona's historical profile and evidence are synthetic examples, explicitly labelled in the UI. New actions run against MongoDB. Reset Demo affects only the demo account.

## Configuration

Use `backend/.env` (template: `backend/.env.example`). Existing process environment variables take priority; the root `.env` is a legacy fallback. Never commit secrets.

- `MONGODB_URI`, `MONGODB_DB`
- `JWT_SECRET`: long random secret. Sessions are signed JWTs in browser sessionStorage, sent as Bearer tokens. Passwords use PBKDF2-SHA256; no fake hashes or test identities.
- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`: backend only. No Ollama, no simulated mentor responses.
- `REVIEWER_EMAILS`: comma-separated registered reviewer emails. This grants privileged review access; do not add the student's own demo account for self-verification.

The currently configured OpenRouter key returned HTTP 401 in a real generation request. Replace it privately in `backend/.env`, then restart the API. Health reports the actual last probe state.

## Evidence and verification rules

- Student uploads/manual records cannot grant themselves Verified status or authoritative scores.
- Resume parsing extracts skill-name/alias matches from actual PDF or UTF-8 text. Claims remain unverified. Scanned PDFs without text need OCR outside this implementation.
- Assessments are graded against server-owned keys. MCQ, multiple-select and short-answer inputs are supported. Existing coding items test code comprehension; arbitrary submitted code is not executed.
- Before-assessment snapshots are persisted. Failed tests do not receive passing floors.
- Project submissions enter Needs Review. An authorized reviewer must inspect the artifact and provide a score and concrete observation for every rubric criterion. A weighted score of at least 80 and every criterion at least 60 produces verified project evidence. Reviewers cannot review their own work. A project URL alone never verifies a skill.
- Verified evidence does not automatically make an entire skill Verified: aggregate mastery and prerequisite rules still apply.
- The resume/ATS scores are platform heuristics, not third-party ATS results or hiring guarantees.

## AI, retrieval and ML

`POST /api/v1/mentor/chat` forwards the actual message and bounded conversation history to the selected server-side provider (Groq or OpenRouter). Typed read-only services assemble current competency/career/roadmap/evidence context. Retrieved document identifiers are validated before returning source references. Service failures remain errors.

The local RAG corpus contains ten curated technical guidance summaries plus public career, skill, resource, assessment and project catalog documents. Shared indexing excludes student documents and answer keys. FAISS performs vector search. Retrieval combines lexical overlap and vector similarity; metadata filtering is available. Documents/chunks and embedding metadata are persisted in MongoDB. Health reports the active embedding backend and vector index. The default offline hashing embedder is genuine lexical vector retrieval, not a semantic transformer. Optional neural dependencies are listed in `requirements-rag.txt`; model download is explicit via `prepare_rag.py` and never happens during a request.

Evidence-strength classification uses multinomial logistic regression and learning-risk advisory uses Ridge regression. Both are exposed through authenticated analytics and the dashboard, with synthetic-data labels and no authority to verify evidence. Recommendation ranking uses scikit-learn Ridge, trained reproducibly on labelled **synthetic demo data**. Train/validation/test splits are 60/20/20. Reported errors measure that synthetic rule only; they are not real learner outcome accuracy. The saved inference model is JSON, with no pickle execution. Ranking never overwrites mastery or readiness.

```powershell
.\.venv\Scripts\python.exe -m app.ml.training.train
.\.venv\Scripts\python.exe -m app.ml.training.advisory
.\.venv\Scripts\python.exe evaluate_rag.py
```

## Validation

```powershell
# Project root
npm.cmd run lint
npm.cmd test
npm.cmd run build

# backend
.\.venv\Scripts\python.exe -m pytest app/tests -q
.\.venv\Scripts\python.exe -m pip check
```

Integration tests use the isolated `career_intelligence_qa` MongoDB database and explicitly labelled QA accounts/artifacts. They exercise signup, ownership, document/PDF parsing, claim spoof rejection, wrong/correct assessment scoring, roadmap/state-version changes, project submission/reviewer authorization, retrieval, resource isolation and diagnostic replay rejection.

See `PROJECT_STATUS.md` for verified results and unresolved requirements. Docker configuration has an API reverse proxy; a full Docker deployment has not been verified. Local rate limiting is per process; cross-worker coordination, transactional crash recovery, exhaustive accessibility and production load/security review remain work before public deployment.

## Competency and resume projections

Authenticated `GET /api/v1/competencies/relationships` exposes the nine typed relationship projections from the canonical student state; `GET /api/v1/competencies/concepts` exposes latest scored topic observations. Missing topic observations are unassessed, not zero. Relationship projections do not grant verification or maintain a second mastery store.

Thirteen assessment banks cover baseline topics plus advanced Python/SQL and introductory HTML/CSS, networking, Linux and Docker. Diagnostics choose the closest available difficulty for current mastery. Coverage remains limited to authored questions.

Resume uploads preserve detected section text and original upload timestamps. Current scoring includes claims from the active uploaded resume; previous documents remain in history. Section extraction and skill matching are conservative heuristics, and scanned PDFs require OCR that is not implemented.

Latest local checkpoint: 28 backend tests and 70 frontend tests pass, including ownership, active-resume replacement, graph provenance and keyboard interaction checks. Frontend testing uses Vitest 5 with Vite 8; the production build and TypeScript check pass. See the status file for remaining external and production validation gates.

## AI Mentor provider configuration

The local configuration now selects Groq (`LLM_PROVIDER=groq`), with `GROQ_MODEL=openai/gpt-oss-120b`. Set `GROQ_API_KEY` privately in `backend/.env`, then restart the backend. Obtain a key from https://console.groq.com/keys. Credentials never belong in frontend environment variables or chat. Real process environment values override `.env`; if rotating a key, update any inherited environment value too.

`LLM_PROVIDER=openrouter` explicitly selects the original adapter. `auto` selects Groq only when its key is configured, otherwise OpenRouter. Failed requests are never silently sent to another provider. Authenticated `GET /api/v1/mentor/status` returns cached provider status; `POST /api/v1/mentor/check` makes a small real generation request. The page offers Check connection, preserves failed questions, excludes failed turns from subsequent context, prevents duplicate sends, and displays supplied source citations. The check can consume a small amount of provider quota.

The OpenRouter key returned HTTP 401 during the live check. Groq is now configured privately and verified with four live provider checks plus an authenticated Mentor response with three retrieved citations. The original OpenRouter adapter remains optional.

After configuring the key, run `.\.venv\Scripts\python.exe verify_mentor_provider.py` from the backend directory. The live smoke checks use synthetic learner context and save `mentor-provider-evaluation.json`; they do not replace human review of answer quality.
