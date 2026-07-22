# Deferred work

Surfaced during quick-dev reviews; not in the scope of the triggering story.

## Touch/tap support for field tooltips
- **Source:** `spec-input-field-tooltips.md` review (2026-07-22), Blind Hunter + Edge Case Hunter.
- **Issue:** `FieldTooltip` uses `@radix-ui/react-tooltip`, which opens on hover and keyboard focus only — not on touch tap. On phones/tablets the per-field help copy is unreachable.
- **Why deferred:** The project is desktop-first (see `project-context.md`) and the tooltip spec scoped its I/O matrix to hover + keyboard + screen-reader. A proper touch fix means switching the info affordance from a Tooltip to a click/tap-driven Popover (`@radix-ui/react-popover`) — an interaction-model change beyond the frozen "tooltip" intent, so it needs a product decision.
- **Suggested fix when picked up:** Replace `FieldTooltip` with a Popover-based `FieldInfo` (click/tap to open, Esc/outside-click to close), keeping the same `label`/`description` API and the `FIELD_HELP`/`PICKER_HELP` copy source. Verify keyboard + screen-reader parity and re-run the axe smoke.
