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
        lint test dev backend frontend presets clean \
        compose-up compose-down

# Local demo defaults — the SPA and API run as separate origins, so CORS on the
# backend must allow the Vite dev server. Override on the command line if needed.
# Independent of the Docker Compose host port (see docker/docker-compose.yml) —
# this is the non-Docker `make backend`/`make web` flow, not the containerized one.
API_PORT := 8000
WEB_ORIGIN := http://localhost:5173

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

backend: ## Start the API (FastAPI/uvicorn, hot-reload) on port 8000
	CORS_ORIGINS=$(WEB_ORIGIN) uv run uvicorn vllm_calc_api.main:app --port $(API_PORT) --reload

frontend: ## Start the web dev server (vite), pointed at the local API
	cd $(WEB) && VITE_API_BASE_URL=http://localhost:$(API_PORT) npm run dev

dev: ## Start the web dev server (vite)
	cd $(WEB) && npm run dev

presets: ## Validate presets (schema + provenance) — same check as CI
	uv run python -m vllm_calc_api.preset_validation

# --- Docker (full stack: backend + frontend) -----------------------------------

COMPOSE := docker compose -f docker/docker-compose.yml

compose-up: ## Build & run the full stack in Docker (SPA on :5173, API on :8350)
	$(COMPOSE) up -d --build

compose-down: ## Stop and remove the Docker stack
	$(COMPOSE) down

compose-logs: ## Show the logs of the Docker stack
	$(COMPOSE) logs -f

compose-ps: ## Show the running containers of the Docker stack
	$(COMPOSE) ps

clean: ## Remove tool caches and web build artifacts
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	rm -rf $(WEB)/dist $(WEB)/tsconfig.tsbuildinfo
