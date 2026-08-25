# Contributing to Employee Exit Survey Analytics

Thanks for your interest! This project follows a small set of conventions to
keep the pipeline reproducible and the history clean.

## Development setup

```bash
git clone https://github.com/hari-qa-svg-development/employee-exit-survey-analytics.git
cd employee-exit-survey-analytics
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

## How to contribute

1. **Fork** the repository and create a branch from `main`
   (`git checkout -b feature/your-change`).
2. Make your change. Add or update **tests** for any pipeline logic in `src/`.
3. Run the full suite locally: `pytest -q`.
4. (Re)generate artifacts if you touched data logic:
   `python scripts/run_pipeline.py`.
5. Commit using a clear, conventional message (see below) and push.
6. Open a **Pull Request** against `main`.

## Commit style

Use short, imperative subject lines:

```
feat: add tenure-band analysis
fix: handle blank length-of-service in TAFE transform
docs: expand README quick start
test: add validation for institute vocabulary
```

## Code style

- Python 3.10+, type hints where they add clarity.
- No unnecessary comments — let the code and tests speak.
- Keep functions pure where possible (the pipeline modules are designed to be
  reused by the notebook, the report generator and the tests).

## Reporting issues

Open an issue with the template that fits:

- **Bug** — what you did, what you expected, what actually happened, and the
  output of `pytest`.
- **Enhancement** — the use case and a proposed approach.

## Code of conduct

Be respectful and constructive. By participating, you agree to uphold a
welcoming environment for everyone.
