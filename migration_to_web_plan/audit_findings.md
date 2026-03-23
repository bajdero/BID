# BID Migration Audit Findings (Baseline)

Date: 2026-03-23
Source documents:
- `migration_to_web_plan/User_story.md`
- `migration_to_web_plan/web_architecture.md`

## 1. Decision Log (Confirmed by Stakeholder)

These decisions are now treated as mandatory requirements for planning and architecture updates.

1. Multi-user support is mandatory from the first release.
2. Search must be semantic/vector-based.
3. Descriptions and tags must be editable in both UI and external API.
4. Deduplication identity is content hash only.
5. Export conflicts must be blocked by default; Admin decides action in UI with options for:
   - single file,
   - multi-selection,
   - apply to all.
6. Automatic quality rating should start with deterministic EXIF-based rules; ML scoring is a later feature.
7. Admin monitoring must include:
   - worker utilization,
   - error rate,
   - queue length.
8. Audit logs must be immutable append-only.
9. Internationalization must cover both EN/PL UI and metadata/tag vocabulary strategy.
10. Add PR workflow stories for curated collections, approval workflow, and scheduled social publish packs.

## 2. Audit Summary Against Current Web Architecture

## 2.1 Implemented or Strongly Covered

- Authentication foundation (`/auth/login`, JWT, refresh flow).
- Event source loading and schedule-based annotation flow.
- Core project/source/processing endpoint skeleton.
- Real-time update channel via WebSocket protocol.

## 2.2 Partially Covered (Requires Expansion)

- Photo filtering: architecture supports source tree/query patterns but not full multi-criteria + negative filtering behavior contract.
- User management and authorization: foundational auth exists, but mandatory day-1 multi-role RBAC is not fully specified end-to-end.
- Processing observability: status flow exists, but worker utilization/error-rate/queue-length telemetry is not fully modeled.
- Automatic export operations: profile config exists, but conflict policy and admin conflict resolution UX/API are incomplete.
- Audit logging: logging exists conceptually, but immutable append-only model and complete filterable audit surface are incomplete.

## 2.3 Not Implemented / Missing

- Semantic/vector search design (indexing pipeline, retrieval API, ranking).
- Description and tag CRUD API model + indexing integration.
- Full PR tag workflow and bulk operations.
- Day-1 multiuser architecture contract (tenant/project scoping, ownership and sharing rules).
- Deterministic EXIF quality score feature model.
- i18n/l10n architecture for EN/PL.
- Export conflict handling workflow (block + admin resolution actions for one/many/all).
- Immutable event configuration history as auditable stream.
- PR curation/approval/scheduled publish-pack workflows.

## 3. Known Bugs Coverage Status

- BUG-01 (reupload same filename not reindexed): unresolved in architecture as written; hash-based identity now confirmed and should address root cause when implemented.
- BUG-02 (cannot overwrite export): policy now clarified as block + explicit admin conflict resolution.
- BUG-03 (unsupported auxiliary files): partially addressed via allowlist notes; needs strict upload-boundary enforcement contract.
- BUG-04 (file not seekable): partially mitigated, but robust upload completion protocol still needed.
- BUG-05 (index while uploading/downloading): partially mitigated with DOWNLOADING state; final consistency rules still required.
- BUG-06 (event manager history missing): unresolved until immutable append-only event change log is implemented.

## 4. Priority Gap Backlog (Draft)

P0 (must be in first implementation wave)
1. Day-1 multi-user RBAC model and enforcement across all endpoints/pages.
2. Hash-only deduplication identity and reindex lifecycle rules.
3. Description/tag CRUD in UI + external API.
4. Semantic/vector search pipeline and query API.
5. Export conflict blocking + admin resolution operations (single/multi/all).
6. Immutable append-only audit/event logs.
7. Queue metrics endpoint + dashboard cards for worker utilization/error rate/queue length.

P1
1. Deterministic EXIF-based rating and score explanation surface.
2. Full EN/PL localization (UI + domain vocabulary governance).
3. PR curation and approval workflow.

P2
1. Scheduled social publish packs.
2. ML-based quality scoring extension.

## 5. Proposed Next Document Updates

1. Extend `User_story.md` with new/clarified stories for:
   - multiuser RBAC (mandatory day-1),
   - semantic search,
   - description/tag API,
   - export conflict resolution,
   - immutable audit/event logs,
   - queue observability,
   - PR curation/approval/scheduled packs,
   - i18n governance.
2. Extend `web_architecture.md` with corresponding architecture sections:
   - authz matrix,
   - vector index service/components,
   - hash dedup pipeline,
   - audit event-store schema,
   - conflict-resolution APIs,
   - observability model.
