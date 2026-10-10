# Target Objective Learning Hub

The existing Resources page now uses MongoDB career requirements plus their transitive skill prerequisites. The competency and roadmap engines are called read-only; reading a chapter or downloading a PDF never awards evidence or mastery. Existing mapped resource bookmark/completion actions remain available.

## Content and downloads

Original AI-assisted English chapters live in `backend/app/assets/learning/<skillId>.json`. Each chapter contains foundations, mapped concepts, worked examples, a process flow, interview preparation, a summary and practice solutions. The reader and ReportLab PDF use the same chapter objects. Full books follow prerequisite order. Bibliographies contain titles/authors only. Linked primary documentation supplies further reading.

A chapter must pass structural, coverage and minimum-length checks before publication. Missing/new/changed competency topics are shown as unavailable, and an incomplete full book returns HTTP 503 instead of being labeled complete. Existing catalog scope is preserved: these books cover the current CareerIQ competency catalog, not every possible topic in a profession. AI-assisted notes should receive continuing subject-matter review; structural tests alone do not establish factual correctness.

Authenticated endpoints:
- GET `/api/v1/learning-hub/{career_id}`
- GET `/api/v1/learning-hub/{career_id}/notes?topic_id=...`
- GET `/api/v1/learning-hub/{career_id}/pdf?topic_id=...`

Omit topic_id for the full book. Unknown careers/topics return 404. Missing prerequisite references/cycles return 422. MongoDB collections `learningTopics`, `learningCareers`, `learningPdfs` and `learningVideos` store versioned content, plans, PDF binary data and verified public video metadata. Content hashes invalidate cached PDFs when their inputs change.

## YouTube without an API key

Public watch-page metadata and oEmbed were used to verify videos, channels, duration and observed view counts. English is supported by default English audio or original English automatic-caption metadata. Recommendations use exact-topic relevance, reputable channels and observed views; level fit further personalizes ties. Counts are dated snapshots, not a claim that every item is globally the highest-viewed video. The UI de-duplicates shared videos and paginates the initial grid.

Approved video metadata is cached for seven days. Stale entries refresh in the background; failed refreshes keep a clearly marked stale snapshot. Known unavailable videos are excluded. No invented counts, runtime AI resource URLs or repeated searches occur in student requests. YouTube availability can subsequently change or vary by region.

## Maintaining the curriculum

`tools/build_learning_notes.py` is an offline authoring helper using the configured Groq credentials. `LEARNING_AUTHOR_MODEL` can select an available authoring model without changing the app mentor model. It skips existing chapters and writes drafts; review mathematical examples, code, factual claims and topic coverage before publication. Do not treat generated prose as automatically reviewed.

`tools/curate_learning_videos.py` discovers candidates for missing topics using a reputable-channel allowlist, checks public metadata and stores only verified results. Review relevance before publication. Add bibliography/discovery terms to `app/services/learning_catalog.py` when introducing catalog skills. Neither script is invoked by a learner request.

PDF generation requires ReportLab and Arial (Windows) or DejaVu fonts (Linux), already supported by the renderer. PDF caches contain study material only, not learner credentials. No unrelated route or competency calculations are changed.

## Validation (1 October 2026)

- All 34 catalog skills have structurally complete chapters and verified public English video metadata; 105 distinct videos are cached across topics.
- All 37 backend tests pass, including five career curricula, full/topic PDF downloads, unchanged competency/evidence state, Mongo persistence, content-cache reuse, personalization and error cases.
- All 103 frontend tests pass (one pre-existing optional live test skipped), including sidebar navigation and learning-hub career changes, topic filters, de-duplication, notes reader, downloads and stale-request handling.
- TypeScript and Vite production build pass. Existing graph/chart test warnings and the ELK chunk-size warning remain outside this feature.
- Live API through port 3000 verified authenticated career data and byte-identical cached PDF responses. Final downloads: AI Engineer 109 pages, ML Engineer 77, Data Scientist 52, Backend Developer 41, Cloud & MLOps Engineer 122.
- PDF cover, contents, code, chapter and reference pages were visually inspected; every page in all five books passed text-boundary checks. Final example downloads are in backend/output/pdf.
- Interactive browser QA was blocked by the browser tool's localhost-access policy. Component/API checks and PDF visual QA were completed; no browser-console or mobile visual pass is claimed.
