---
title: 'Fix local port conflict on the Docker Compose backend'
type: 'bugfix'
created: '2026-08-11'
status: 'done'
route: 'one-shot'
---

# Fix local port conflict on the Docker Compose backend

## Intent

**Problem:** `docker compose up` bound the backend service to host port 8000, which collided with another local process on the developer's machine, blocking the full-stack local run.

**Approach:** Remap the backend's host-side port to 8350 in `docker/docker-compose.yml` (the container-internal port stays 8000, since that traffic never touches the host), and update every place that documents or defaults to the old host-facing URL — `docker/README.md`, the `Makefile`'s `compose-up` comment, and the CLI's `DEFAULT_API_URL` — so the documented zero-config "run compose, then run the CLI" flow keeps working.

## Suggested Review Order

**Host port remap**

- Entry point: only the host side of the mapping changes (`8000:8000` → `8350:8000`); the container keeps listening on 8000 internally.
  [`docker-compose.yml:17`](../docker/docker-compose.yml#L17)

- Comment documenting the CLI-facing URL, kept in sync with the mapping above.
  [`docker-compose.yml:8`](../docker/docker-compose.yml#L8)

**Keeping the CLI's zero-config default in sync**

- The CLI's built-in `--api-url` default must match the compose-exposed host port, or the documented no-flags CLI flow breaks.
  [`main.py:20`](../packages/cli/src/vllm_calc_cli/main.py#L20)

**Documentation updates**

- Full-stack and standalone `docker run` examples updated to the new host port.
  [`README.md:32`](../docker/README.md#L32)
  [`README.md:35`](../docker/README.md#L35)
  [`README.md:45`](../docker/README.md#L45)

- `compose-up` target comment updated; a new comment clarifies `API_PORT` is a separate, unrelated port space for the non-Docker dev flow.
  [`Makefile:18`](../Makefile#L18)
  [`Makefile:93`](../Makefile#L93)

- Historical Dev Agent Record annotated (not rewritten) to point at the current default.
  [`epics.md:611`](epics.md#L611)

**Peripherals**

- Two review findings logged for later pickup (stale `make docker-up` doc references; no safeguard against the host port and CLI default drifting apart again).
  [`deferred-work.md`](deferred-work.md)
</content>
