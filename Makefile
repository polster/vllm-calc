# Makefile — local dev environment for vllm-calc.
#
# Mirrors the commands CI runs (.github/workflows/ci.yml) so a green `make check`
# locally means green CI. Python uses uv (workspace + committed uv.lock); the web
# side uses npm. See CONTRIBUTING.md for the toolchain rationale.

WEB := web

.DEFAULT_GOAL := help
.PHONY: help setup setup-python setup-node \
        check check-python check-web \
        hooks-install hooks-uninstall hooks-run \
        lint test dev presets clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# --- Setup ---------------------------------------------------------------------

setup: setup-python setup-node hooks-install ## Set up the whole dev env (Python + web + git hooks)

setup-python: ## Sync the Python workspace from uv.lock
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; }
	uv sync

setup-node: ## Install web dependencies (npm)
	@command -v npm >/dev/null 2>&1 || { \
		echo "npm not found. Install Node 22+ (matches CI: .github/workflows/ci.yml)."; \
		exit 1; }
	cd $(WEB) && npm install

# --- Checks (parity with CI) ---------------------------------------------------

check: check-python check-web ## Run the full CI suite locally

check-python: ## Python: ruff + mypy + pytest + preset validation
	uv run ruff check .
	uv run mypy .
	uv run pytest
	uv run python -m vllm_calc_api.preset_validation

check-web: ## Web: lint + typecheck + test + build
	cd $(WEB) && npm run lint && npm run typecheck && npm test && npm run build

# --- Pre-commit hooks ----------------------------------------------------------

hooks-install: ## Install the git pre-commit hooks
	uv run pre-commit install

hooks-uninstall: ## Remove the git pre-commit hooks
	uv run pre-commit uninstall

hooks-run: ## Run all pre-commit hooks against every file
	uv run pre-commit run --all-files

# --- Handy shortcuts -----------------------------------------------------------

lint: ## Lint Python + web
	uv run ruff check .
	cd $(WEB) && npm run lint

test: ## Test Python + web
	uv run pytest
	cd $(WEB) && npm test

dev: ## Start the web dev server (vite)
	cd $(WEB) && npm run dev

presets: ## Validate presets (schema + provenance) — same check as CI
	uv run python -m vllm_calc_api.preset_validation

clean: ## Remove tool caches and web build artifacts
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf $(WEB)/dist $(WEB)/tsconfig.tsbuildinfo
