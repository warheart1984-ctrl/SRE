# Contributing to Sovereign Reconstruction Engine

Thank you for helping improve SRE. This repository combines an open constitutional
framework (Apache-2.0) with separately licensed Mythar creative assets — see
[docs/ip/README.md](docs/ip/README.md).

## Development setup

Requirements: Python 3.11+

```bash
git clone <repo-url>
cd sovereign-reconstruction-engine
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,api]"
pytest -q
```

Optional API dependencies are in the `[api]` extra. Copy `.env.example` to `.env` when
running the HTTP API or Dantomax signing locally.

## Code style

- **Lint:** `ruff check src/ packages/ tests/`
- **Format fixes:** `ruff check --fix src/ packages/ tests/`
- Match existing module layout: domain code in `src/sre/`, FAE substrate in `packages/fae/`,
  integration boundary in `src/sre/substrate/`.

## Testing

```bash
pytest -q                          # SRE + substrate (default)
pytest tests/test_fra_mcrl_composition.py -v   # FAE composition path
pytest tests/test_cih_conformance.py -q        # CIH conformance profile
```

FAE package self-tests under `packages/fae/tests` are present but not part of the
default green gate — run them explicitly when changing vendored FAE code.

## Documentation evidence (Drive-G)

Documentation claims must not exceed implementation evidence. When updating docs:

- Assert only what code, tests, schemas, or configs prove.
- Label roadmaps and aspirations explicitly.
- Prefer weaker verbs when evidence is partial (`aligns with`, `tests`, `planned`).
- Canonical rule: `docs/governance/DriveG_DocumentationEvidenceLaw.md`.

## Pull requests

1. Fork and branch from `main`.
2. Keep changes focused; include tests for behavior changes.
3. Update `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
4. Ensure `pytest -q` and `ruff check src/ packages/ tests/` pass locally.
5. Open a PR with a clear summary and test plan.

## Mythar content

Do not treat Mythar lexicon, cosmology, or publishable bundle files as open-source.
Framework contributions that touch Mythar data should preserve licensing boundaries
documented in `docs/mythar/publishable/README.md`.

## Security

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).
