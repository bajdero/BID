## Problem Statement

Production deployment requires Kubernetes manifests for scalable, reliable hosting.

## Scope

**In scope:**
- Kubernetes Deployment, Service, and Ingress manifests for backend and frontend
- ConfigMap and Secret templates
- Horizontal Pod Autoscaler for backend
- Namespace and RBAC configuration

**Out of scope:**
- Cloud provider-specific managed services (use generic k8s)

## Acceptance Criteria

- [ ] Manifests deploy successfully to a staging Kubernetes cluster
- [ ] HPA scales backend pods under load
- [ ] Secrets managed via k8s Secret (not hardcoded)

## Dependencies

- **Milestone:** M11 — Test/Deploy Readiness (Phase 8)
- **Depends on:** P8-03 (Docker images)
- **Parent epic:** [Epic] Phase 8 — Test/Deploy Readiness

## Definition of Done

- [ ] Manifests committed to `deploy/k8s/`
- [ ] Tested on staging cluster
- [ ] Merged to `main`
