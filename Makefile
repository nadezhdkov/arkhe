# ─────────────────────────────────────────────────────────────────────────────
#  arkhe — Makefile (uv workspace)
# ─────────────────────────────────────────────────────────────────────────────
#  Targets:
#    make test        → Run all tests
#    make build       → Build all packages (sdist + wheel)
#    make build-PKG   → Build a single package (e.g. make build-arkhe-meta)
#    make rebuild     → Clean + build all
#    make clean       → Remove build artifacts
#    make publish     → Upload ALL packages to PyPI
#    make publish-PKG → Upload a single package (e.g. make publish-arkhe-meta)
#    make lint        → Run ruff linter
#    make format      → Run ruff formatter
#    make check       → lint + test
#    make version     → Show current package version
#    make sync        → Sync the uv workspace
# ─────────────────────────────────────────────────────────────────────────────

# Load .env if it exists (exports PYPI_TOKEN, etc.)
ifneq (,$(wildcard .env))
    include .env
    export
endif

# All packages in the workspace
PACKAGES := $(wildcard packages/*)
PACKAGE_NAMES := $(notdir $(PACKAGES))

.PHONY: test test-all build rebuild clean publish lint format check version help sync

# ── Default ──────────────────────────────────────────────────────────────────

help: ## Show this help
	@echo ""
	@echo "  arkhe — available targets"
	@echo "  ─────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Packages: $(PACKAGE_NAMES)"
	@echo ""

# ── Sync ─────────────────────────────────────────────────────────────────────

sync: ## Sync the uv workspace (install all packages)
	uv sync --all-packages

# ── Test ─────────────────────────────────────────────────────────────────────

test: ## Run all tests
	uv run pytest tests/ -v --tb=short

# ── Build ────────────────────────────────────────────────────────────────────

build: test ## Build all packages (sdist + wheel)
	@for pkg in $(PACKAGES); do \
		echo "\n\033[36m▸ Building $$(basename $$pkg)...\033[0m"; \
		uv build --package $$(basename $$pkg); \
	done
	@echo "\n\033[32m✓ All packages built successfully.\033[0m"

build-%: ## Build a single package (e.g. make build-arkhe-meta)
	uv build --package $*

# ── Rebuild ──────────────────────────────────────────────────────────────────

rebuild: clean build ## Clean then build all

# ── Clean ────────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf dist/
	@for pkg in $(PACKAGES); do \
		rm -rf $$pkg/dist/ $$pkg/build/ $$pkg/*.egg-info; \
	done
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f .coverage
	rm -rf .pytest_cache htmlcov

# ── Publish ──────────────────────────────────────────────────────────────────

publish: rebuild ## Upload ALL packages to PyPI (requires PYPI_TOKEN in .env)
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Add it to .env: PYPI_TOKEN=pypi-xxx)
endif
	@for pkg in $(PACKAGES); do \
		pkg_name=$$(basename $$pkg); \
		echo "\n\033[36m▸ Publishing $$pkg_name...\033[0m"; \
		uv run python -m twine upload dist/$$pkg_name-* \
			--username __token__ \
			--password $(PYPI_TOKEN) \
			--non-interactive \
			--verbose; \
	done
	@echo "\n\033[32m✓ All packages published.\033[0m"

publish-%: ## Upload a single package (e.g. make publish-arkhe-meta)
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Add it to .env: PYPI_TOKEN=pypi-xxx)
endif
	uv build --package $*
	uv run python -m twine upload dist/$*-* \
		--username __token__ \
		--password $(PYPI_TOKEN) \
		--non-interactive \
		--verbose

# ── Lint / Format ────────────────────────────────────────────────────────────

lint: ## Run ruff linter on all packages
	uv run ruff check packages/ tests/

format: ## Run ruff formatter on all packages
	uv run ruff format packages/ tests/

# ── Combined ─────────────────────────────────────────────────────────────────

check: lint test ## Lint + test

# ── Info ─────────────────────────────────────────────────────────────────────

version: ## Show current package version
	@uv run python -c "from arkhe.version import __version__; print(__version__)"
