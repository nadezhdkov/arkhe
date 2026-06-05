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

publish: ## Show available publish targets
	@echo ""
	@echo "Available publish targets:"
	@echo "─────────────────────────────────────────"
	@for pkg in $(PACKAGE_NAMES); do \
		echo " make publish-$$pkg"; \
	done
	@echo ""
	@echo "Short aliases:"
	@echo " make publish-config"
	@echo " make publish-core"
	@echo " make publish-db"
	@echo " make publish-game"
	@echo " make publish-log"
	@echo " make publish-math"
	@echo " make publish-meta"
	@echo " make publish-net"
	@echo " make publish-os"
	@echo " make publish-scheduler"
	@echo " make publish-web"
	@echo ""
	@echo "Publish everything:"
	@echo " make publish-all"
	@echo ""

publish-all: rebuild ## Upload ALL packages to PyPI (requires PYPI_TOKEN in .env)
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Add it to .env: PYPI_TOKEN=pypi-xxx)
endif
	@for pkg in $(PACKAGES); do \
		pkg_name=$$(basename $$pkg); \
		pkg_name_norm=$$(echo $$pkg_name | tr '-' '_'); \
		echo "\n\033[36m▸ Publishing $$pkg_name...\033[0m"; \
		uv run python -m twine upload dist/$$pkg_name_norm-* \
			--username __token__ \
			--password $(PYPI_TOKEN) \
			--non-interactive \
			--skip-existing; \
		echo "\033[33mWaiting 20 seconds...\033[0m"; \
		sleep 20; \
	done
	@echo "\n\033[32m✓ All packages published.\033[0m"

publish-%: ## Upload a single package (e.g. make publish-arkhe-meta)
ifndef PYPI_TOKEN
	$(error PYPI_TOKEN is not set. Add it to .env: PYPI_TOKEN=pypi-xxx)
endif
	@echo "\n\033[36m▸ Building $*...\033[0m"
	uv build --package $*
	@pkg_name_norm=$$(echo $* | tr '-' '_'); \
	echo "\n\033[36m▸ Publishing $*...\033[0m"; \
	uv run python -m twine upload dist/$$pkg_name_norm-* \
		--username __token__ \
		--password $(PYPI_TOKEN) \
		--non-interactive \
		--skip-existing

# ── Friendly aliases ─────────────────────────────────────────────────────────

publish-config:
	@$(MAKE) publish-arkhe-config

publish-core:
	@$(MAKE) publish-arkhe-core

publish-db:
	@$(MAKE) publish-arkhe-db

publish-game:
	@$(MAKE) publish-arkhe-game

publish-log:
	@$(MAKE) publish-arkhe-log

publish-math:
	@$(MAKE) publish-arkhe-math

publish-meta:
	@$(MAKE) publish-arkhe-meta

publish-net:
	@$(MAKE) publish-arkhe-net

publish-os:
	@$(MAKE) publish-arkhe-os

publish-scheduler:
	@$(MAKE) publish-arkhe-scheduler

publish-web:
	@$(MAKE) publish-arkhe-web

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
