# api/Makefile — every Python command in this project goes through uv.
#
# UV_PROJECT_ENVIRONMENT is exported here because uv accepts it only as an
# environment variable; it cannot be set in pyproject.toml. The environment must
# be `venv`, not uv's default `.venv` — see ADR-026 and the README.

export UV_PROJECT_ENVIRONMENT := venv

.PHONY: sync test lint fmt run clean check-dotvenv

## sync   — create/refresh venv/ from uv.lock, including the dev group
sync: check-dotvenv
	uv sync

## test   — run the test suite
test: check-dotvenv
	uv run pytest

## lint   — ruff + black in check mode, as CI runs them
lint: check-dotvenv
	uv run ruff check .
	uv run black --check .

## fmt    — apply ruff's fixes and black's formatting
fmt: check-dotvenv
	uv run ruff check --fix .
	uv run black .

## run    — the B1 visible outcome: list recent mail
run: check-dotvenv
	uv run schedule-manager list --limit 10

## clean  — remove the environment and caches
clean:
	chflags -R nohidden venv .venv 2>/dev/null || true
	rm -rf venv .venv .pytest_cache .ruff_cache

# A stray .venv means someone ran uv directly instead of through make. It will
# work today and break silently in a week, so refuse to build on top of it.
check-dotvenv:
	@if [ -d .venv ]; then \
		echo "error: .venv exists. uv was run outside make."; \
		echo "       A dot-prefixed environment gets the macOS hidden flag under"; \
		echo "       this iCloud folder, and Python then skips the editable .pth."; \
		echo "       Run 'make clean && make sync'."; \
		exit 1; \
	fi
