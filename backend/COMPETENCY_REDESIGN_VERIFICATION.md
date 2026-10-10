# Competency Intelligence redesign

Scope: presentation and interactions on the existing competency page, including its skill inspector. Existing competency calculations, persisted evidence, career requirements and assessment baseline remain the data sources. No backend or database migration.

Implemented:
- Collapsed domain overview with career-path expansion, domain expansion and collapse/reset controls.
- Career Path, Domain Map, All Skills and Before vs Current views.
- Live readiness, verification, progress, critical-gap and next-skill summary.
- Domain/state/required/gap filters and search that focuses the chosen skill.
- Lazy-loaded ELK layered layout, orthogonal prerequisite edges, compact cards, pan/zoom/fit controls.
- Skill inspector with target, mastery, confidence, evidence, prerequisites, requirement explanation and learning actions.
- Responsive grouped skill lists below the desktop breakpoint; baseline comparison retained.

Automated verification:
- Full frontend suite: 88 tests passed across 10 test files with `LIVE_API_TEST=1`.
- TypeScript (`npm run lint`) and production build (`npm run build`) passed.
- Layout fixtures contain 30 and 50 skills with branching prerequisites. Checks cover card separation, edge/card collisions, orthogonal routing, left-to-right flow, preservation of input values and cycle-safe prerequisite traversal.
- Component checks cover collapsed defaults, expansion/collapse, search, filters, inspector opening, reset, baseline comparison and Learn Next navigation.
- Additional regression check covers Ctrl-wheel cancellation/zoom and clearing the requirement explanation on reset.
- Follow-up checks cover collapsing a searched skill, collapsing a single domain from All Skills, and returning from baseline comparison to current career-path values. Removed toolbar clipping of search results, allowed action buttons to wrap, and made domain selection exit the relevant-path filter.
- Recovery checks render the actual App, provider, sidebar and all ten lazy-loaded pages in jsdom, navigate back to Dashboard and remount with a retained session. Both fixture state and the current MongoDB demo snapshot pass without captured console.error calls. The live snapshot also passes ELK card-separation checks. This is component integration coverage, not a real-browser end-to-end claim.
- Local competency fixes restrict historical values to the comparison view and discard the previous layout while arranging a replacement. Regression tests cover retained historical mode and an ELK failure falling back to an accessible skill list.

App recovery diagnosis:
- At inspection, ports 3000 and 8000 had no listeners; MongoDB on 27017 was running. Restarted the existing Vite and FastAPI services. Both are listening again.
- No `.git` repository is present, so no historical Git diff is available. No shared navigation defect was reproduced in the authenticated integration checks; App.tsx, sidebar, global state and competency calculations were left unchanged.

Limits:
- Live browser visual QA could not be completed: the browser tool rejected the localhost tab under its URL security policy. No alternate browser access was attempted. Mobile/tablet appearance and rendered label readability still need visual confirmation.
- Geometry checks prevent cards overlapping and edges passing through unrelated cards for the fixtures. They do not guarantee that edges in a complex dependency graph never cross each other.
- ELK produces a large lazy-loaded build chunk; Vite reports a chunk-size warning. The layout library is loaded when skills are expanded.
