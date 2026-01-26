---
name: firebase-functions
description: Rules for Firebase Cloud Functions with TypeScript. Focus: correctness, security, idempotency, observability, and maintainable boundaries. Avoid unnecessary architecture and boilerplate.
stack:
  - TypeScript
  - Firebase Cloud Functions
  - Firestore / Auth (optional)
---

# Firebase Cloud Functions Rules — TypeScript

This document defines the authoritative rules for this functions codebase.

Principle: **Strict at boundaries, pragmatic in implementation.**

---

## 1. Operating Modes (Context-Aware Strictness)

### A. HTTP Mode
Applies to:
- HTTP functions (public/private endpoints)
- Callable functions (client-invoked)

### B. Trigger Mode
Applies to:
- Firestore triggers
- Auth triggers
- Pub/Sub / Scheduler triggers
- Storage triggers

**Rule:** Trigger mode requires stronger idempotency + retries awareness.

---

## 2. Baseline Standards

- TypeScript with strict typechecking (`strict: true` recommended).
- Prefer Functions v2 style (where applicable) and modern Firebase Admin SDK usage.
- Do not rely on implicit `any`.
- Prefer small functions with clear boundaries.

---

## 3. Contract-First (Recommended, not dogmatic)

When creating a new capability:
1) Define a minimal **Request/Response contract** (types/interfaces) first.
2) Define a minimal **Service interface** when there is external I/O (DB, network, payments).
3) Implement the service.
4) Wire into the function handler.

Exceptions:
- Tiny helpers with no I/O do not need interfaces.

Goal: make it easy to review and test the contract before implementation.

---

## 4. Input Validation (Mandatory)

All external inputs must be validated:
- HTTP body, query params, headers
- Callable `data`
- Trigger event payloads (defensive checks)

Rules:
- Validate at the edge.
- Reject early with clear error shape.
- Never trust client-provided UID, role, or price.

Recommended: schema validation (e.g. Zod) for HTTP/callable.

---

## 5. Authentication & Authorization (Mandatory where user context exists)

### HTTP
- If endpoint is not public, require auth (ID token verification).
- Authorization must be explicit (roles/claims checks).
- Avoid “security by obscurity” (no hidden query flags).

### Callable
- Treat `context.auth` as the only trustworthy user identity.
- Do not accept UID from `data` as identity.

---

## 6. Firestore & Data Rules

- Use server timestamps where relevant.
- Prefer transactions for read-modify-write.
- Avoid multiple round trips when a transaction or batched write is appropriate.
- Never do unbounded reads in a single invocation without pagination/limits.

---

## 7. Idempotency & Retries (Mandatory for Trigger Mode)

Cloud Functions can retry. Triggers can deliver duplicate events.

Rules:
- All side-effecting operations must be idempotent.
- Use an idempotency key:
  - event ID, document path + update time, or a generated operation ID stored in DB.
- If you call external services, store a “completed” marker to avoid repeats.

---

## 8. Errors & Status Codes

### HTTP
- Use correct status codes:
  - 400 invalid input
  - 401 unauthenticated
  - 403 unauthorized
  - 404 not found (avoid leaking existence if needed)
  - 409 conflict (idempotency collisions)
  - 429 rate limit
  - 500 internal errors
- Return a stable JSON error shape.

### Callable
- Throw explicit typed callable errors (do not leak internal stack traces).

Rule: never return raw error objects.

---

## 9. Logging & Observability (Mandatory)

- Log structured data (fields), not string dumps.
- Never log secrets, tokens, or PII.
- Include correlation fields:
  - requestId / traceId if available
  - userId (only if safe)
  - function name + operation name

If you add metrics/tracing, keep it centralized.

---

## 10. Secrets & Config (Mandatory)

- Do not hardcode API keys.
- Use environment config / secrets mechanism.
- Secrets must not be logged.
- If a secret is missing, fail fast with clear error.

---

## 11. Performance & Cost

- Avoid large dependency imports in hot paths.
- Cache expensive singletons at module scope when safe.
- Prefer minimal reads/writes per request.
- For heavy CPU work:
  - keep it bounded
  - consider moving to dedicated processing (queue) if it grows

---

## 12. Testing (Recommended)

- Prefer emulator-based tests for Firestore/Auth flows.
- Unit test pure logic and validation.
- Mock external APIs at the service boundary.
- Do not hit production from tests.

---

## 13. Anti-Patterns (Forbidden)

- Trusting client input without validation
- Using client-supplied UID as identity
- Non-idempotent triggers that call external services
- Logging tokens, secrets, or sensitive user data
- Unbounded Firestore queries in one invocation
- Swallowing errors silently

---

## 14. Agent Conduct (Meta Rules)

Agents must:
- Keep changes minimal and scoped.
- Prefer small, reviewable diffs.
- Use "suggest/consider" for optimizations.
- Use "must/never" only for correctness/security.

If unsure, ask for the contract and edge behavior first.