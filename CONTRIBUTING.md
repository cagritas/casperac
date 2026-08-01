# Contributing to CasperAC

First off, thanks for taking the time to contribute! 🎉

## Development Setup

1. Fork the repo and clone it locally.
2. Install dependencies in editable mode:
   ```bash
   pip install -e .
   pip install ruff black
   ```
3. Create a branch for your feature/bugfix.
4. Make your changes.
5. Format your code with Black: `black .`
6. Lint your code with Ruff: `ruff check . --fix`
7. Push to your fork and submit a Pull Request.

## Coding Style
- We use **Black** for code formatting (PEP 8 compliant).
- We use **Ruff** for fast linting.
- Ensure all public functions have docstrings.
- Use type hints (`typing` module) wherever possible.
