# SUB-34 Implementation Evidence: Upload And Processing Jobs

Status: Implemented; verification pending

## Scope

- Authenticated NGO Preparer multipart upload UI and API for CSV, XLSX, PDF, PNG, and JPEG.
- Extension/media-type validation, non-empty check, and 10 MB limit before registration.
- Immutable hashed artifact registration in PostgreSQL/MinIO followed by a real PostgreSQL ingestion job.
- Worker claims queued work with row locking, records running/attempt state, verifies stored bytes, and finishes completed or actionable failed.
- UI polls the real job endpoint and displays queued, running, completed, or failed state.
- Identical organization/contract/filename/content retry returns the existing job rather than creating duplicate processing work.

## Authority And Failure Boundaries

- Only NGO Preparer may create upload jobs; reads are server-scoped by organization.
- Playwright and UI cannot set job state or inject processed records.
- Failed jobs retain an error code/message; downstream import/extraction stories own idempotent domain writes.

## Verification Required

- Each allowed document family queues and reaches completion through the worker.
- Invalid type, mismatched media type, empty, and oversized input fail visibly.
- Identical retry returns the same job/artifact.
- Unauthorized creation and cross-organization reads fail without mutation.
- React renders upload controls and live status for NGO Preparer only.
