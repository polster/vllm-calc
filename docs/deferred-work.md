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

## No safeguard against Docker Compose host ports drifting from their documented/hardcoded references
- **Source:** `spec-fix-docker-port-conflict.md` review (2026-08-11) and `spec-fix-docker-frontend-port-conflict.md` review (2026-08-11), adversarial review.
- **Issue:** Both Docker Compose host ports — backend (`docker/docker-compose.yml`, also duplicated in the CLI's `DEFAULT_API_URL` in `packages/cli/src/vllm_calc_cli/main.py`) and frontend (`docker/docker-compose.yml`, also duplicated in `docker/README.md` and the `Makefile`'s `compose-up` comment) — are hand-maintained literals with nothing binding their copies together. This is exactly what caused two separate port-conflict fixes on the same day (2026-08-11) to each require several manual, unenforced file edits, and nothing stops a future edit to any one copy from silently breaking the others.
- **Why deferred:** Fixing this properly means either making both host ports configurable via env vars (with a `.env.example`) or adding a test/CI check asserting all copies agree — both are design decisions beyond a one-shot fix.
- **Suggested fix when picked up:** Add `BACKEND_HOST_PORT` (default `8350`) and `FRONTEND_HOST_PORT` (default `8360`) to `docker/docker-compose.yml` as `"${BACKEND_HOST_PORT:-8350}:8000"` / `"${FRONTEND_HOST_PORT:-8360}:80"`, document both in `docker/README.md`'s config table, and/or add a test that fails if any documented/hardcoded copy of either port ever diverges from the compose file.

## Engine's `SUPPORTED_VLLM_RANGE` is stale relative to newer presets' `vllm_version_checked`
- **Source:** `spec-add-glm-5.2-preset.md` review (2026-09-07), adversarial review.
- **Issue:** `packages/engine/src/vllm_calc_engine/constants.py`'s `SUPPORTED_VLLM_RANGE` is pinned to `">=0.13,<0.14"`, but the new `glm-5.2.yaml` preset's `vllm_version_checked: "0.23"` reflects the real minimum vLLM version needed to serve GLM-5.2 (per vLLM's own recipe page) — nearly ten minor versions past what the app claims to support. This preset is not the first to drift past the pin; it's just the largest jump so far.
- **Why deferred:** Bumping `SUPPORTED_VLLM_RANGE` is an app-wide compatibility claim (surfaced via `CalcResult.supported_vllm_range` and `VLLM_VERSION_RANGE` env override) that needs its own verification pass across all presets, not a side effect of adding one model.
- **Suggested fix when picked up:** Audit all presets' `vllm_version_checked` values, decide the real supported vLLM range for the app as a whole, and update `SUPPORTED_VLLM_RANGE` (or document why presets are allowed to individually exceed it).
