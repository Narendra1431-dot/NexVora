# Editable profile and avatars

The existing Profile & Vault card now opens an Edit Profile dialog with Save/Cancel. Name, headline, degree, college, GPA, graduation year, weekly learning hours, summary, prior experience, academic details and learning preferences persist through the authenticated profile API. Draft and saved-profile Undo/Redo remain available.

Readiness display source is an optional career selection used only on the profile card. It follows the current learning target by default. All displayed readiness values come from existing competency/evidence calculations; selecting a display source does not change the learning target or permit editing a score.

The avatar picker offers 16 original inline vector designs across student, coder, AI, generic hero, minimal, initials, scholar and explorer styles. No copyrighted character/logo assets or external avatar services are used. Selected avatars update the profile card, sidebar and top-bar avatar after saving.

Photo workflow: choose JPG/PNG/WebP (5 MB maximum, 16 megapixels maximum), preview, square crop using zoom/horizontal/vertical controls, then Save Avatar. The server decodes and re-encodes the image as a metadata-free 384px WebP, storing the small image in the owned MongoDB profile document. Invalid formats, oversize files and invalid image data are rejected. Photo display errors fall back to initials. Remove/Reset Photo is previewed before Save Avatar commits the reset.

Endpoints: PUT /api/v1/profile/avatar, POST /api/v1/profile/photo, DELETE /api/v1/profile/avatar. Avatar fields cannot be injected through the general profile PATCH endpoint. Avatar image data is excluded from copilot tool projections.

Validation: 43 backend tests passed; 117 frontend tests passed (one optional live navigation test skipped in the full run); TypeScript and production build passed. A separate live test through localhost:3000 verified profile save/refresh, preset selection, photo upload and reset persistence. Component tests cover Save/Cancel, selection preview, crop coordinates, validation, upload and broken-photo fallback. Browser/mobile visual inspection remains unverified because of the previously reported browser-access restriction.
