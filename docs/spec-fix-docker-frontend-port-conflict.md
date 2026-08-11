---
title: 'Fix local port conflict on the Docker Compose frontend'
type: 'bugfix'
created: '2026-08-11'
status: 'done'
route: 'one-shot'
---

# Fix local port conflict on the Docker Compose frontend

## Intent

**Problem:** `docker compose up` bound the frontend (nginx-served SPA) service to host port 5173, which collided with another local process on the developer's machine — the same class of conflict fixed for the backend service in `spec-fix-docker-port-conflict.md`.

**Approach:** Remap the frontend's host-side port to 8360 in `docker/docker-compose.yml` (the container-internal port stays 80, since nginx inside the container and that traffic never touches the host), and update `docker/README.md` and the `Makefile`'s `compose-up` comment to match. Also added a short troubleshooting note to `docker/README.md` since this is now the second host-port collision in a row.

## Suggested Review Order

**Host port remap**

- Only the host side of the mapping changes (`5173:80` → `8360:80`); the container keeps listening on 80 internally.
  [`docker-compose.yml:32`](../docker/docker-compose.yml#L32)

- Comment documenting the SPA URL, kept in sync with the mapping above.
  [`docker-compose.yml:6`](../docker/docker-compose.yml#L6)

**Documentation updates**

- SPA URL updated to the new host port.
  [`README.md:30`](../docker/README.md#L30)

- New troubleshooting note: this is the second port collision found on this stack, so a pointer to the fix pattern is now documented directly.
  [`README.md:40`](../docker/README.md#L40)

- `compose-up` target comment updated.
  [`Makefile:93`](../Makefile#L93)

**Peripherals**

- Broadened an existing deferred-work item (hand-maintained, unenforced port literals) to cover the frontend port too, since it hit the exact same failure mode as the backend fix.
  [`deferred-work.md`](deferred-work.md)
