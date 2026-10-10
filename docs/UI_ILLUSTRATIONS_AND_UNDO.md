# Typography and edit history

Decorative illustrations were removed at the user's request. The current UI uses self-hosted Inter with Manrope headings, system fallbacks and locally included OFL licenses. The shared illustration component and generated scene assets were deleted. Existing certificate designs and edit-history behavior are unchanged.


- Global Undo/Redo controls appear in the top bar, with equivalent controls inside onboarding, resume and certificate dialogs for keyboard/focus accessibility.
- Shortcuts: Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z, Ctrl/Cmd+Y. Unconnected inputs retain native editing shortcuts.
- Draft coverage: onboarding profile fields/career selection, evidence fields/notes, resume paste, certificate display name/subtitle, external credential fields, project description/repository and mentor input.
- Server-backed coverage: saved profile fields and target-career changes. Restoring a career calls the existing backend endpoint so the roadmap is recalculated using current evidence. Newer server values are checked before restoration; conflicting edits produce a recoverable error instead of an overwrite.
- History is session-only, bounded to 80 entries and cleared on account changes or demo reset. Adjacent typing within 700 ms is grouped. New edits invalidate redo. Closed/unmounted editor drafts are removed from history. Programmatic imports/resets do not become accidental edits.
- Assessments, reviewed evidence, resource completion, certificate issuance/payment and uploaded resume analysis are not rolled back. The roadmap is evidence-derived and exposes no manual mastery-edit operation; undo of career selection regenerates it rather than restoring stale scores.
- Failed asynchronous undo retains the command for retry and reports an error. Duplicate replay is disabled while an undo/redo operation is pending.
