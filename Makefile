# ─────────────────────────────────────────────────────────────────────────────
#  nestifypy — Makefile
# ─────────────────────────────────────────────────────────────────────────────
#  Targets:
#    make test      → Run all tests with coverage
#    make build     → Build sdist + wheel
#    make rebuild   → Clean + build
#    make clean     → Remove build artifacts
#    make publish   → Upload to PyPI (reads PYPI_TOKEN from .env)
#    make lint      → Run ruff linter
#    make format    → Run black formatter
#    make check     → lint + test
#    make version   → Show current package version
# ─────────────────────────────────────────────────────────────────────────────

# Load .env if it exists (exports PYPI_TOKEN, etc.)
ifneq (,$(wildcard .env))
    include .env
    export
endif

.PHONY: test build rebuild clean publish lint format check version help

# ── Default ──────────────────────────────────────────────────────────────────

help: ## Show this help
	@echo ""
	@echo "  nestifypy — available targets"
	@echo "  ─────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Test ─────────────────────────────────────────────────────────────────────

test: ## Run all tests with coverage
	uv run pytest tests/ \
		--ignore=tests/test_komodo.py \
		--ignore=tests/test_loom.py \
		--ignore=tests/test_nestify.py \
		--ignore=tests/test_pyunix.py \
		-v --tb=short

test-all: ## Run ALL tests (including unstable ones)
	uv run pytest tests/ -v --tb=short

# ── Build ────────────────────────────────────────────────────────────────────

build: test-all ## Build sdist + wheel into dist/
	uv run python -m build

# ── Rebuild ──────────────────────────────────────────────────────────────────

rebuild: clean build ## Clean then build

# ── Clean ────────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f .coverage
	rm -rf .pytest_cache htmlcov

# ── Publish ──────────────────────────────────────────────────────────────────

publish: rebuild ## Upload to PyPI (requires PYPI_TOKEN in .env)
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Add it to .env: PYPI_TOKEN=pypi-xxx)
endif
	uv run python -m twine upload dist/* \
		--username __token__ \
		--password $(PYPI_TOKEN) \
		--non-interactive

# ── Lint / Format ────────────────────────────────────────────────────────────

lint: ## Run ruff linter
	uv run ruff check src/ tests/

format: ## Run black formatter
	uv run black src/ tests/

# ── Combined ─────────────────────────────────────────────────────────────────

check: lint test ## Lint + test

# ── Info ─────────────────────────────────────────────────────────────────────

version: ## Show current package version
	@python -c "from src.nestifypy.version import __version__; print(__version__)"
