# Deferred work

Surfaced during quick-dev reviews; not in the scope of the triggering story.

## Touch/tap support for field tooltips
- **Source:** `spec-input-field-tooltips.md` review (2026-07-22), Blind Hunter + Edge Case Hunter.
- **Issue:** `FieldTooltip` uses `@radix-ui/react-tooltip`, which opens on hover and keyboard focus only — not on touch tap. On phones/tablets the per-field help copy is unreachable.
- **Why deferred:** The project is desktop-first (see `project-context.md`) and the tooltip spec scoped its I/O matrix to hover + keyboard + screen-reader. A proper touch fix means switching the info affordance from a Tooltip to a click/tap-driven Popover (`@radix-ui/react-popover`) — an interaction-model change beyond the frozen "tooltip" intent, so it needs a product decision.
- **Suggested fix when picked up:** Replace `FieldTooltip` with a Popover-based `FieldInfo` (click/tap to open, Esc/outside-click to close), keeping the same `label`/`description` API and the `FIELD_HELP`/`PICKER_HELP` copy source. Verify keyboard + screen-reader parity and re-run the axe smoke.

## Stale `make docker-up`/`make docker-down` references
- **Source:** `spec-fix-docker-port-conflict.md` review (2026-08-11), adversarial review.
- **Issue:** `docker/docker-compose.yml`'s header comment and `docker/README.md`'s "Full stack" section both tell readers to run `make docker-up` / `make docker-down`, but the Makefile only defines `compose-up` / `compose-down`. Pre-existing, not caused by the port-conflict fix that surfaced it.
- **Why deferred:** Out of scope for a one-shot port config change; needs its own small doc fix.
- **Suggested fix when picked up:** Either rename the Makefile targets to `docker-up`/`docker-down`, or fix the two doc references to say `compose-up`/`compose-down`.

## No safeguard against the backend host port and CLI default drifting apart
- **Source:** `spec-fix-docker-port-conflict.md` review (2026-08-11), adversarial review.
- **Issue:** The Docker Compose backend's host-exposed port (`docker/docker-compose.yml`) and the CLI's `DEFAULT_API_URL` (`packages/cli/src/vllm_calc_cli/main.py`) are two independently hand-maintained literals with nothing binding them together — this is exactly what caused the 2026-08-11 port-conflict fix to require four manual file edits, and nothing stops a future edit to one from silently breaking the other.
- **Why deferred:** Fixing this properly means either making the host port configurable via an env var (with a `.env.example`) or adding a test/CI check asserting the two values agree — both are design decisions beyond a one-shot fix.
- **Suggested fix when picked up:** Add `BACKEND_HOST_PORT` (default `8350`) to `docker/docker-compose.yml` as `"${BACKEND_HOST_PORT:-8350}:8000"`, document it in `docker/README.md`'s config table, and/or add a test that fails if `DEFAULT_API_URL`'s port and the compose file's host port ever diverge.
