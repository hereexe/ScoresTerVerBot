# Repository Guidelines

## Project Structure & Module Organization
This repository is currently minimal: `README.md`, `.gitignore`, and `.context/plane.md` (project plan). The target layout (per the plan) is a Python Telegram bot with modules under `bot/` (e.g., `bot/handlers/`, `bot/config.py`) and tests under `tests/`. If you add or move directories, update this document to match the real structure.

## Build, Test, and Development Commands
No build or task runner is configured yet. Once the scaffold exists, use these expected commands:
- `pip install -r requirements.txt` to install dependencies.
- `python main.py` to run the bot locally.
- `pytest` to run tests.
If you introduce a tool like `pyproject.toml`, add the exact commands here.

## Coding Style & Naming Conventions
Follow PEP 8 with 4‑space indentation and type hints for public functions. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Prefer explicit async boundaries (`async def`) and avoid blocking I/O inside handlers. No formatter or linter is configured yet; if you add one (e.g., `ruff`, `black`), document the version and usage.

## Testing Guidelines
Testing is expected to use `pytest` with files named `tests/test_*.py`. Focus on FSM flows, input validation, and aggregation logic. Mock external services (Telegram API, MongoDB) where possible and keep tests deterministic.

## Commit & Pull Request Guidelines
Git history currently contains only “Initial commit,” so no convention is established. Use short, imperative commit subjects (e.g., “Add lecture admin command”), and include a scope if helpful. PRs should include a clear summary, reasoning, test steps, and linked issues. For dialog changes, include a short example chat transcript or screenshot.

## Security & Configuration Tips
Store secrets in `.env` and never commit tokens. Document required variables in `.env.example` (e.g., `BOT_TOKEN`, `MONGODB_URI`, `DB_NAME`, `ADMINS`). Use a least‑privilege MongoDB user for production.

## Agent Notes
If you are an automated agent, consult `.context/plane.md` for the agreed roadmap and keep this guide aligned with actual repo structure.
