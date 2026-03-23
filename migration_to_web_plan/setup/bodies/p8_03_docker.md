## Problem Statement

The application must be containerised so that it runs identically in development,
staging, and production, eliminating environment-specific bugs.

## Scope

**In scope:**
- `Dockerfile` for FastAPI backend (multi-stage, non-root user)
- `Dockerfile` for React frontend (Nginx serving static build)
- `docker-compose.yml` for local development (backend + frontend + DB)
- Docker image builds in CI and pushed to container registry

**Out of scope:**
- Kubernetes manifests (P8-04)

## Acceptance Criteria

- [ ] `docker-compose up` starts a working local environment
- [ ] Backend image size < 500 MB
- [ ] Images built and pushed in CI on merge to `main`
- [ ] Images run as non-root user

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] Dockerfiles committed
- [ ] `docker-compose up` verified locally
- [ ] CI pipeline pushes images
- [ ] Merged to `main`
