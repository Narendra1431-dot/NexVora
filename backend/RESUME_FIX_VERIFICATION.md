# Resume Intelligence verification

Scope: existing Resume Intelligence page and its supporting ingestion/state APIs. Layout retained.

- Styled PDF/TXT chooser and drop area, paste validation, busy locking, success/error recovery and same-file retry.
- Active-document claims only; one claim per mapped catalog skill. Replacements preserve proof/history and exclude old resume claims from current analysis.
- Persisted analysis uses the selected MongoDB career and current verifier evidence. Evidence IDs link to proof, never to the resume claim itself.
- ATS heuristic: 40% recognized section structure + 40% weighted selected-role keyword coverage + 20% verified-claim coverage. Role match is resume keyword coverage, distinct from career readiness.
- Empty analysis/cards hidden. Missing role keywords, counts, sections and suggested improvements derive from actual analysis.
- Export separates self-reported resume text and unsupported claims from verified skills. Copy reports failure honestly; download uses a direct Markdown link.

Validation: 29 backend tests and 75 frontend tests passed, TypeScript and production build passed. Real demo PDF lifecycle test covers parsing, MongoDB persistence, role change, real assessment proof, invalid replacement, TXT replacement, duplicate uploads and zero-claim resumes. Browser PDF upload produced 12 claims (1 verified, 11 unverified) and 6 sections on the seeded demo. ATS 49, role keyword match 38%, evidence coverage 8% at that evidence snapshot. Browser recommendations, copied draft and exact Python gap navigation verified. Scanned-PDF OCR is unsupported; no external ATS result or hiring guarantee is claimed.

Browser limitation: the in-app browser did not emit a download event or save a visible file during Markdown download checks. Direct download link content/filename are tested; clipboard copy and export preview were verified live. Native file saving remains unverified in this browser.
