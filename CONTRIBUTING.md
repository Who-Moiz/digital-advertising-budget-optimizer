# Contributing

Open an issue for a significant behavior change, then work on a focused branch.
Install with `python -m pip install -e ".[dashboard,dev]"`. Before submitting, run:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
```

Add meaningful tests for KPI changes, allocation invariants and backend parity.
Keep undefined ratios explicit, preserve total budget at paisa precision, and do
not commit large generated files or real customer information. Describe behavior
and validation in pull requests. Be respectful and specific in reviews.
