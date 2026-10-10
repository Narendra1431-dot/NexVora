# Certificate system

The existing app now includes My Certificates and public `/certificate/{certificateId}` pages. `npm run dev` serves port 5000. The existing port 3000 process can remain open during development. Backend API remains on port 8000.

## Configuration

- `PUBLIC_APP_URL=http://localhost:5000` is the requested local origin. It is read by the backend when issuing each immutable certificate. Use an externally reachable HTTPS origin before issuing certificates intended for other devices. Localhost links only work on the issuing computer; changing this variable does not rewrite previously issued PDFs or links.
- `CERTIFICATE_PAYMENT_MODE=demo` enables an explicit no-charge purchase simulation. Demo price: INR 199. The order, confirmation, UI, public viewer and PDF label DEMO purchases. No real provider or payment credentials are configured. Other payment modes fail closed; implement a provider with server-side verification before enabling live payments.
- New runtime packages: reportlab and qrcode. No new frontend packages.

## Eligibility and authority

Only `Course` resources qualify. The backend reads student-owned `resourceProgress` and server-scored assessment attempts, requiring passing scores and matching verified assessment evidence. Catalog courses can specify `certificatePolicy.moduleIds`, `certificatePolicy.assessmentIds`, and the supported `completionRule: all_modules_and_assessments`. Without an explicit policy, the course itself is the single completion unit and the first assessment by ID for the same skill is required. A course with no assessment remains locked. External course completion is self-reported learning activity, not independent mastery evidence.

The presentation-only certificate agent produces allow-listed metadata and template choices. It cannot grade, authorize payment or decide eligibility. Verified skills come from current competency state backed by qualifying assessment evidence. A pass can earn a completion certificate while prerequisites still prevent full competency verification; such certificates clearly say full verification is pending.

## Persistence, security and evidence

`certificates` stores immutable student/course snapshots, proof IDs, template version, status, payment state, completion/issuance dates and PDF bytes. Unique indexes enforce both certificate ID and student/course/type uniqueness. IDs contain 128 random bits. Retrying issuance returns the existing record, including after concurrent requests. Free and premium are separate editions.

`certificateOrders` stores student/course ownership, server price, mode, confirmation and 30-minute expiry. Premium generation requires a confirmed, unexpired, owned order. Only displayName and optional displaySubtitle are editable before issuance. Scores, skills, course details, dates, IDs and payment status remain backend-owned.

Each issued edition has one idempotent Evidence Vault reference linked to course, assessments and original proof IDs. It has no skillId and is excluded by the existing competency evidence index: the same assessment does not increase mastery or confidence twice. Listing/issuance retries repair an interrupted evidence-reference write.

Public APIs return only an explicit certificate-safe allow-list, excluding internal student ID, private evidence IDs, order ID, Mongo fields and PDF storage bytes. Anyone with the random public link can view the certificate name and achievement; this is intentional public verification. Invalid or non-valid IDs return a generic 404. QR and PDF endpoints read the persistent registry record without authentication. Public App rendering happens before the authentication provider; Vite and the existing Nginx fallback support refreshed deep links.

Premium PDFs have an electronic issuer signature area. They are not cryptographically signed PDFs and do not claim to be.

## API

- GET `/api/v1/certificates` (authenticated)
- GET `/api/v1/certificates/eligibility/{course_id}` (authenticated)
- POST `/api/v1/certificates/generate` (authenticated; courseId, type, optional orderId)
- POST `/api/v1/certificates/premium/create-order` (authenticated; courseId)
- POST `/api/v1/certificates/premium/confirm` (authenticated; orderId, confirmDemo)
- GET `/api/v1/certificates/{id}` (public safe record)
- GET `/api/v1/certificates/{id}/pdf` (public PDF)
- GET `/api/v1/certificates/{id}/qr` (public vector QR)
- GET `/api/v1/certificates/verify/{certificateId}` (public verification)

## Validation

Backend integration uses only the isolated `career_intelligence_qa` MongoDB database. Tests cover incomplete/failed/passed conditions, additional required modules, unsupported rules, forged fields, PDF output, persistence, evidence reference and unchanged competency values, duplicate issuance, public and invalid IDs, separate anonymous clients, premium confirmation, foreign orders, expired orders and disabled live payments.

Frontend tests cover premium preview/order/confirmation/generation sequencing, locked controls, public deep-link remount without login, invalid IDs, copying links, PDF download initiation, and all sidebar pages.

Free and premium A4 landscape PDFs were rendered to PNG and inspected. Live browser visual QA is still limited by the browser tool's URL policy rejection; component integration tests are not a substitute for real-browser/device checks. Cross-device access remains a deployment configuration step because the requested origin is localhost.

Final checks: 93 frontend tests passed with LIVE_API_TEST=1; TypeScript and production build passed. Full backend suite: 31 passed. Final certificate integration retest: 2 passed. Live certificate-list API and invalid-ID 404 checks passed after restarting FastAPI. Free/premium PDFs were visually inspected after completion dates were added. Browser/device visual checks remain pending as described above.

## Demo certificate previews
My Certificates includes Preview Demo Certificate, with standard/premium template switching, viewport full-screen mode, 50–200% zoom, fit width, sample PDF download and Close/Escape controls. Read-only /demo/{free|premium}/pdf and /preview.png endpoints render the production PDF template with explicit SAMPLE markings. PDF-to-PNG rendering uses PyMuPDF. Sample QR codes lead to /demo/info, never an issued certificate record. No database or evidence operations occur; DEMO-CERT-001 is invalid for real verification.

## Locked premium reference template
Premium version careeriq-premium-locked-v1 uses app/assets/certificates/premium-locked-v1.png, derived from the supplied navy/gold reference with variable text removed. Dynamic text uses matching Times serif typography and reference coordinates on A4 landscape. Preview and issuance use the same PDF renderer; the public preview PNG is rendered directly from the stored PDF bytes. Existing issued snapshots are immutable and retain their original template. Standard certificates retain their existing design.

POST /api/v1/certificates/preview validates authenticated eligibility and accepts only courseId, type, displayName and displaySubtitle. It writes no records. GET /api/v1/certificates/{id}/preview.png renders the stored PDF. Display fields are snapshotted on issuance and cannot alter verified fields. Issued premium PDFs omit sample disclaimers; demo payment status remains explicit in the surrounding UI and API.

Locked-template validation: TypeScript and production build pass; frontend suite 95 passed/1 optional live test skipped, followed by 9 certificate component tests passed after adding server-preview coverage. Three MongoDB/PDF certificate tests passed. Sample and issued premium PDFs rendered and visually inspected. Restarted API serves the updated premium PDF and PNG. Browser QA remains blocked by the existing tool URL policy.
