# Coding Space integration

This module adds `/coding-space`, `/coding-space/practice`, and `/coding-space/games` within the existing authenticated app. Vite and production SPA hosting must serve the app entry for those routes.

## Isolated general-purpose execution

Set these privately in `backend/.env`, then restart FastAPI:

```
JUDGE0_URL=https://your-private-judge0-service
JUDGE0_AUTH_TOKEN=your-service-token
```

For a RapidAPI-backed Judge0 instance, optionally set `JUDGE0_RAPIDAPI_KEY` and `JUDGE0_RAPIDAPI_HOST`. Never use a public shared runner for confidential code without reviewing its privacy terms. No credentials enter the frontend.

The adapter follows the official [Judge0 CE API](https://ce.judge0.com/docs). Requests disable networking and set 2-second CPU, 5-second wall, 128 MB memory, 64 MB stack and 64 KB file limits. Judge0 must itself run on a correctly configured, patched, isolated host. The app never invokes a local interpreter, compiler, shell, exec or eval for submissions. Missing/unavailable runner means a visible error, no fake result and no XP.

The catalog supports Python, Java, C, C++ and JavaScript using standard Judge0 CE language IDs. A runner deployment with a different language catalog must adapt the mapping in `app/coding/catalog.py`.

## Games

Five games have 17 levels in total. Mission Script is explicitly a **restricted teaching language**, not unrestricted Python. Its AST interpreter accepts only bounded integer arithmetic, assignments, range loops, if/else, zero-argument functions, and documented game commands. There are no imports, attributes, host calls, file access, or network access. Limits apply to source size, AST size, instruction count, function depth, loop count and trace size. All mission completion decisions run server-side. Run previews only; Submit Mission records success.

Algorithm Race animates actual swaps of the chosen built-in sorting routine. Array Defender animates packet filtering. Bug Hunter runs bounded print/range/assignment exercises. Grid games replay server-produced positions.

## XP integrity and ranking

`xpTransactions` is the single source for overall NexVora XP. A unique `(studentId, sourceType, sourceId)` index prevents duplicate rewards, including simultaneous submits. Progress documents and `codingStats`/profile totals are projections; ranks are calculated from the shared ledger, not invented demo values. Student name alone is shown on the leaderboard; emails, credentials and source code are not public.

The pre-existing app had no learner XP/rank system. Existing passed assessments earn 50 activity XP once per assessment and recorded completed resources 10 once per resource when synced. This does not alter assessment scores, competency calculations or evidence verification. Coding rewards do not automatically confer mastery.

First-attempt success adds 20 practice XP. Daily completion adds 20 once per UTC date, even if the underlying task was previously completed. Practice base XP never repeats. Game level rewards and efficiency bonuses are in one idempotent transaction. Achievements are recognition badges, without repeatable bonuses. Streaks use dates of successful coding/game transactions in UTC.

The catalog starts with 13 original practice problems and 5 games; unsupported categories are not filled with fake items. Problems and game definitions are seeded in MongoDB. Hidden practice tests are excluded from all public detail, run, and AI responses.

## Editor and persistence

Monaco is installed locally, with local workers and language assets; no CDN dependency. JavaScript supports its language-service formatter; other languages explicitly report whitespace normalization instead of claiming a full formatter. Keyboard shortcuts: Ctrl/Cmd+Enter Run, Ctrl/Cmd+Shift+Enter Submit, Escape exits fullscreen. Browser-native selection/copy and Monaco undo remain intact.

Code is saved immediately on the current device and debounced to MongoDB by student/task/language. Client timestamps reject older autosaves. Local recovery remains available if the server is unreachable. Font size persists with the draft; language preference is student-specific. Pending saves also flush when leaving a task. Failed synchronization retains a device-local recovery copy; the UI reports this distinction.

## Verification

Run `python -m pytest app/tests/test_coding.py -q` from backend. These test real MongoDB in the isolated `_qa` database, all game levels, input restrictions, ownership, draft ordering, hidden-test sanitization, failed/accepted/duplicate submissions, concurrent rewards, daily bonuses and rank changes. General-purpose judge responses are mocked for deterministic contract tests; this is not proof of live runner availability. Live five-language execution remains pending until a real Judge0 configuration is supplied.

### Local verification, 4 October 2026

TypeScript and production build passed (Monaco/ELK chunk-size advisories remain). Frontend navigation, resume and profile regression suite: 10 passed, 1 opt-in live test skipped. Backend integration suite: 2 passed, exercising all 17 mission solutions and MongoDB reward/draft contracts. Browser checks covered real robot Run/Submit, duplicate submission with zero additional XP, level unlock, refresh persistence, font size, fullscreen, JavaScript formatting, Groq hint response, 390px mobile, 820px tablet and 1440px desktop. No browser console errors observed. Judge0 was not configured, so live practice compilation/execution and accepted-code AI review remain pending. Games Completed counts fully finished games; Missions Completed counts individual levels.
