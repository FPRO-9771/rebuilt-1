---
name: Use .venv for tests
description: Always run pytest and other Python commands using the .venv virtual environment
type: feedback
---

Run tests using the .venv virtual environment, not the system Python.

**Why:** The project dependencies (phoenix6, robotpy, etc.) are installed in .venv, not globally.

**How to apply:** Prefix Python commands with `.venv/bin/python` or activate the venv first. For example: `.venv/bin/python -m pytest tests/ -v`
