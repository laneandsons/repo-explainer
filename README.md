# repo-explainer

## Setup

Install dependencies:

```sh
uv sync
```

## Run

```sh
uv run python main.py
```

## Add a dependency

```sh
# Runtime dependency
uv add <package>

# Development-only dependency
uv add --dev <package>
```

## Test

```sh
uv run pytest
```

## Build

```sh
uv build
```

---

## uv quick reference

| Task                        | Command                        |
|-----------------------------|--------------------------------|
| Install dependencies        | `uv sync`                      |
| Run a script                | `uv run python main.py`        |
| Add a runtime dependency    | `uv add <package>`             |
| Add a dev dependency        | `uv add --dev <package>`       |
| Remove a dependency         | `uv remove <package>`          |
| Show installed packages     | `uv pip list`                  |
| Run tests                   | `uv run pytest`                |
| Build a distributable       | `uv build`                     |
| Pin a Python version        | `uv python pin <version>`      |

> uv manages the `.venv/` directory automatically. You do not need to activate
> it manually — `uv run` handles that for every command above.

## Stack

| Layer | Choice | Note |
| :--- | :--- | :--- |
| Python | 3.12 | In the cloud base image |
| Tooling | `uv` | Deps, venv, lockfile, and runner in one — also preinstalled |
| Config | `pyproject.toml` | The only config file you need |
| CLI | `typer` | Argparse if you'd rather have zero deps |
| Repo fetching | `httpx` + stdlib `tarfile` | Download the tarball; no need to shell out to `git` |
| LLM | `anthropic` | First-class Python SDK |
| Response parsing | `pydantic` | The real reason to prefer Python here |
| HTML output | `jinja2` | Cleaner than f-strings for a whole page |
| Tests | `pytest` + `syrupy` | Snapshot testing for the rendered HTML |
| Lint + format | `ruff` | One tool, same role Biome played |
| Logging | `structlog` | Structured JSON, sets up the telemetry ticket later |

```
repo-explainer/
  src/repo-explainer/
    fetch/      — owner/repo → local file tree
    analyze/    — file tree → structured summary (no LLM)
    llm/        — summary → explanation (prompt, call, validate)
    render/     — explanation → HTML
    cli/        — wires the four together
  evals/        — fixture repos plus snapshot assertions
  .claude/
    settings.json
    hooks/
    skills/
  pyproject.toml
```

## Skills to install

# Download SKILL.md and place in your agent's skills folder
curl -o SKILL.md https://github.com/trailofbits/skills/tree/main/plugins/modern-python/skills/modern-python/raw/main/SKILL.md