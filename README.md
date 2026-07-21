# Sovereign Reconstruction Engine (SRE) v1.0.0

A constitutional, evidence-governed system for historical and linguistic reconstruction.
SRE implements the CIEMS sovereignty stack: evidence validation (FAC-E), reconstruction
validation (FAC-V), the nine-stage FRA loop, MCRL alignment, and CIH governance.

**License:** Apache-2.0 for the framework · Mythar creative assets are separately licensed
(see [docs/ip/README.md](docs/ip/README.md)).

## What you get

| Layer | Package | Role |
|-------|---------|------|
| Substrate | `fae` / `sre.substrate` | FAC evidence registry, FRA cycle, drift, validation, MCRL Rosetta |
| Domain | `sre.*` | Linguistic evidence, ChronologicalReconstruction, CEL/Dantomax, corpora |
| API | `sre.api` | FastAPI HTTP surface + constitutional explorer |

**Wired today:** FAE is vendored under `packages/fae`. ACCEPTED linguistic evidence mirrors
into the FAE registry. `FRAComposedReconstruction.run_recursive()` drives SRE stage groups
through `SREGovernedFRACycle` with FAC-V2–V4 validation on the integration test path.

See [`docs/architecture/FAESubstrate.md`](docs/architecture/FAESubstrate.md) for evidence-bound status.

## Quick start

```bash
git clone <repo-url>
cd sovereign-reconstruction-engine
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev,api]"
cp .env.example .env               # optional: API / Dantomax / KMS settings
pytest -q
python scripts/run_local.py --corpus mythar
```

Windows (PowerShell): same commands; use `.venv\Scripts\Activate.ps1`.

### HTTP API

```bash
pip install -e ".[api]"
sre-api
# or: python -m sre.api
# Default: http://127.0.0.1:8010
```

OpenAPI spec: [`docs/specs/openapi.yaml`](docs/specs/openapi.yaml).

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SRE_DATA_DIR` | *(repo `data/`)* | Corpus JSON directory when not using a dev checkout |
| `SRE_API_HOST` | `127.0.0.1` | API bind address |
| `SRE_API_PORT` | `8010` | API port |
| `SRE_API_RELOAD` | off | Hot reload for dev (`true` / `1`) |
| `SRE_CEL_STORE_PATH` | in-memory | Persistent CEL ledger file |
| `SRE_DANTOMAX_KEY` | generated | Local HMAC signing key (dev only) |
| `SRE_KMS_MODE` | `local` | `local` or `remote` signing |
| `SRE_KMS_URL` | — | Remote KMS endpoint when `SRE_KMS_MODE=remote` |
| `SRE_KMS_AUTH` | — | Authorization header for remote KMS |

Copy [`.env.example`](.env.example) for a annotated template.

## Corpora

| ID | File | Notes |
|----|------|--------|
| `mythar` | `data/fra_corpus_v01.json` | Synthetic FRA fixture |
| `mythar-lex` | `data/mythar_lexicon_v01.json` | Lexicon clusters (dev reference; Mythar IP) |
| `ie` | `data/ie_cognate_mini_v01.json` | Latin / Spanish / French / Sanskrit mini-corpus |

```bash
python scripts/run_local.py --corpus mythar
python scripts/run_local.py --corpus mythar-lex
python scripts/run_local.py --corpus ie --dantomax --with-cih
```

## Constitutional foundations

1. No constitutional decision without constitutional evidence.
2. All evidence must pass FAC-E1 → FAC-E4 validation.
3. All reconstructions must pass FAC-V1 → FAC-V5 validation.
4. All AI outputs must be evidence-constrained and governance-traceable.
5. All services must operate under Sovereign Certificate authority.

## Promotion status

| Gate family | Status |
|-------------|--------|
| FAC-E1–E4 | Live |
| FAC-V1–V5 | Live (composed cycle path tested) |
| FRA-01–04 | Live (Mythar + IE mini-corpus) |
| AI-01–04 | Live (rule-based, evidence-anchored) |
| CIH-01–05 | Live |

Details: [`docs/governance/PromotionPlan_v01.md`](docs/governance/PromotionPlan_v01.md).

## Documentation map

- **Framework (open):** [`docs/README.md`](docs/README.md) — specs, architecture, governance
- **Mythar (licensed):** [`docs/ip/README.md`](docs/ip/README.md) — not part of Apache-2.0
- **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Changelog:** [`CHANGELOG.md`](CHANGELOG.md)

## Development

```bash
make install-api    # or: pip install -e ".[dev,api]"
make test
make lint
make run            # mythar demo
make smoke          # import check
```

## License

- **SRE framework** (code, specs, open docs): [Apache License 2.0](LICENSE)
- **Mythar language assets:** [LICENSES/Mythar_License.md](LICENSES/Mythar_License.md)

Trademarks and Mythar creative works remain proprietary regardless of framework license.
