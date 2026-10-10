# External certifications

My Certificates now separates CareerIQ Certificates, External Certifications and My Added Credentials. The existing issuance/payment/PDF system is unchanged. Catalog cards use provider initials, with no downloaded trademark assets. All provider links were opened and checked on 2026-09-30. Cisco is explicitly labeled as a certification family. Levels are omitted when the source does not specify one.

## Official sources

- [AWS Certified Developer - Associate](https://aws.amazon.com/certification/certified-developer-associate/)
- [Google Cloud Associate Cloud Engineer](https://cloud.google.com/learn/certification/cloud-engineer)
- [Microsoft Azure AI Cloud Developer Associate](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-cloud-developer-associate/)
- [HashiCorp Terraform Associate](https://developer.hashicorp.com/certifications)
- [Linux Foundation CKAD](https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/)
- [GitHub Foundations Certification](https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/)
- [MongoDB Associate Developer Certification](https://learn.mongodb.com/pages/mongodb-associate-developer-exam)
- [freeCodeCamp JavaScript Certification](https://www.freecodecamp.org/learn/javascript-v9)
- [freeCodeCamp Responsive Web Design](https://www.freecodecamp.org/learn/responsive-web-design-v9)
- [freeCodeCamp Python](https://www.freecodecamp.org/learn/python-v9)
- [freeCodeCamp Relational Databases](https://www.freecodecamp.org/learn/relational-databases-v9)
- [Cisco Certification Exams](https://www.cisco.com/site/us/en/learn/training-certifications/exams/index.html)
- [Red Hat RHCSA](https://www.redhat.com/en/services/certification/rhcsa)

The freeCodeCamp curriculum URLs were followed from its official Python certification announcement: https://www.freecodecamp.org/news/freecodecamps-new-python-certification-is-now-live/. Provider pages remain authoritative for current requirements; CareerIQ does not issue these external awards.

## Persistence and verification

`externalCredentials` stores one owned record per student/catalog certification, credential ID/URL, dates, private proof bytes and reviewer audit metadata. Editing supports corrections and renewal. Unique indexes prevent duplicate additions. MongoDB proof uploads are bounded to 5 MB and validated as readable PDF/PNG/JPEG; downloads require the owner's JWT and force an attachment. IDs, ownership, review state and provider metadata cannot be supplied by clients. User URLs are restricted to HTTP(S) and never fetched by the server.

New records show Added. Only a separate reviewer account listed in REVIEWER_EMAILS can mark Verified through the review endpoint. Expired takes precedence when the supplied expiry date has passed. Editing resets verification. Self-reported dates and IDs are not provider confirmation. A single linked Certificate entry appears in the Profile Evidence Vault; it has no skill ID and cannot raise mastery/confidence. The credential and its evidence are written idempotently; listing repairs any interrupted evidence write.

## APIs (authenticated)

- GET /api/v1/external-certifications — official catalog and caller-owned credentials.
- POST /api/v1/external-certifications/credentials — multipart payload JSON + optional proof.
- PUT /api/v1/external-certifications/credentials/{id} — edit own credential; existing proof retained unless replaced.
- GET /api/v1/external-certifications/credentials/{id}/proof — private proof download.
- POST /api/v1/external-certifications/credentials/{id}/review — authorized independent reviewer only; decision Verified/Unverified and an audit note.

The public CareerIQ certificate registry never contains these external records.

## Validation

Component tests cover all 13 details/official links, categories, tabs, empty states, form values, upload, edit/cancel, download and server errors. MongoDB integration covers persistence, ownership, invalid fields/URLs/dates/proof, size limits, duplicate prevention, review authorization, expiry, renewal and unchanged competency state. Existing CareerIQ issuance tests and sidebar navigation are included in regression runs. Browser visual/device QA remains blocked by the existing browser-tool URL policy, so component checks do not claim actual browser verification.

Final run: 99 frontend tests passed, one optional live-snapshot test skipped; all 33 backend tests passed; TypeScript and production build passed. Authenticated live catalog checks passed directly and through both Vite proxies (3000 and 5000); existing CareerIQ certificate listing passed.
