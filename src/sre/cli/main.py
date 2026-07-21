"""SRE CLI — python -m sre <command> [options]"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import click

from .. import __version__
from ..corpus.ingest import ingest_file
from ..corpus.loader import list_evidence_ids, seed_registry_from_corpus
from ..evidence.cel import CELEntryType, ConstitutionalEvidenceLedger
from ..evidence.dantomax_client import DantomaxClient
from ..evidence.registry import EvidenceRegistry
from ..fra.reconstruction_engine import ChronologicalReconstruction
from ..governance.cih_service import FAECLanguageReconstructionService
from ..linguistics.correspondence_engine import CorrespondenceEngine
from ..linguistics.features import FEATURES
from ..linguistics.phylogeny import build_phylogeny, compute_distance_matrix
from ..linguistics.tokenization import tokenize

# Ensure UTF-8 so IPA characters display on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


class _SortedHelp(click.Group):
    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(super().list_commands(ctx))


@click.group(cls=_SortedHelp)
@click.version_option(version=__version__, prog_name="sre")
def cli() -> None:
    """Sovereign Reconstruction Engine — constitutional linguistic reconstruction."""


# ── serve ───────────────────────────────────────────────────────────


@cli.command(help="Start the SRE HTTP API server")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address")
@click.option("--port", default=8010, type=int, show_default=True, help="Bind port")
@click.option("--reload/--no-reload", default=False, help="Auto-reload on code changes")
def serve(host: str, port: int, reload: bool) -> None:
    import os

    os.environ.setdefault("SRE_API_HOST", host)
    os.environ.setdefault("SRE_API_PORT", str(port))
    if reload:
        os.environ["SRE_API_RELOAD"] = "1"
    from ..api.__main__ import main as _api_main

    _api_main()


# ── evidence ────────────────────────────────────────────────────────


@cli.group(cls=_SortedHelp, help="Manage evidence in the registry")
def evidence() -> None:
    pass


@evidence.command("submit", help="Submit a single evidence record")
@click.argument("evidence_id")
@click.argument("evidence_type", default="corpus_sample")
@click.argument("content_json")
@click.option("--submitted-by", default="cli", show_default=True)
def evidence_submit(
    evidence_id: str, evidence_type: str, content_json: str, submitted_by: str
) -> None:
    registry = _get_registry()
    try:
        content = json.loads(content_json)
    except json.JSONDecodeError:
        click.echo("Error: content_json must be valid JSON", err=True)
        sys.exit(1)
    ev = registry.add_evidence(
        {
            "evidence_id": evidence_id,
            "evidence_type": evidence_type,
            "content": content,
            "submitted_by": submitted_by,
        }
    )
    status = registry.get_status(evidence_id)
    click.echo(
        json.dumps(
            {
                "evidence_id": ev.evidence_id,
                "sha256_hash": ev.sha256_hash,
                "status": status.value if status else "unknown",
            },
            indent=2,
        )
    )


@evidence.command("get", help="Get evidence record by ID")
@click.argument("evidence_id")
def evidence_get(evidence_id: str) -> None:
    registry = _get_registry()
    ev = registry.get_evidence(evidence_id)
    if ev is None:
        click.echo(f"Evidence '{evidence_id}' not found", err=True)
        sys.exit(1)
    click.echo(
        json.dumps(
            {
                "evidence_id": ev.evidence_id,
                "type": ev.evidence_type.value,
                "content": ev.content,
                "sha256_hash": ev.sha256_hash,
                "status": registry.get_status(evidence_id).value
                if registry.get_status(evidence_id)
                else None,
            },
            indent=2,
        )
    )


@evidence.command("validate", help="Re-run FAC-E validation on stored evidence")
@click.argument("evidence_id")
def evidence_validate(evidence_id: str) -> None:
    registry = _get_registry()
    result = registry.revalidate_evidence(evidence_id)
    click.echo(
        json.dumps(
            {
                "evidence_id": result.evidence_id,
                "is_valid": result.is_valid,
                "failed_checks": result.failed_checks,
                "report": result.report,
            },
            indent=2,
        )
    )


@evidence.command("ingest", help="Ingest a JSONL/CSV/corpus-JSON file")
@click.argument("path", type=click.Path(exists=True, path_type=str))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["jsonl", "csv", "json"]),
    default=None,
    help="Override auto-detection",
)
@click.option("--lang", default="und", help="Language code for CSV import")
def evidence_ingest(path: str, format: str | None, lang: str) -> None:
    registry = _get_registry()
    p = Path(path)
    if format == "csv":
        from ..corpus.ingest import ingest_csv

        rows = ingest_csv(registry, p, language_code=lang)
        click.echo(json.dumps({"format": "csv", "ingested": len(rows)}, indent=2))
    elif format == "jsonl":
        from ..corpus.ingest import ingest_jsonl

        rows = ingest_jsonl(registry, p)
        click.echo(json.dumps({"format": "jsonl", "ingested": len(rows)}, indent=2))
    else:
        result = ingest_file(registry, p, format=format)
        click.echo(json.dumps(result, indent=2))


# ── cel ─────────────────────────────────────────────────────────────


@cli.group(cls=_SortedHelp, help="Constitutional Evidence Ledger")
def cel() -> None:
    pass


@cel.command("head", help="Show CEL ledger head")
def cel_head() -> None:
    cel = _get_cel()
    click.echo(json.dumps(cel.summary(), indent=2))


@cel.command("list", help="List CEL entries")
@click.option("--type", "-t", "entry_type", help="Filter by entry type")
@click.option("--subject", help="Filter by subject ID")
@click.option("--limit", default=50, type=int, show_default=True)
def cel_list(entry_type: str | None, subject: str | None, limit: int) -> None:
    cel = _get_cel()
    entries = cel.query(
        entry_type=CELEntryType(entry_type) if entry_type else None,
        subject_id=subject,
        limit=limit,
    )
    click.echo(
        json.dumps(
            {
                "count": len(entries),
                "entries": [e.to_dict() if hasattr(e, "to_dict") else dict(e) for e in entries],
            },
            indent=2,
        )
    )


@cel.command("lineage", help="Show attestation→certification lineage for a reconstruction")
@click.argument("reconstruction_id")
def cel_lineage(reconstruction_id: str) -> None:
    cel = _get_cel()
    lineage = cel.query_lineage(reconstruction_id)
    click.echo(json.dumps(lineage, indent=2))


# ── cih ─────────────────────────────────────────────────────────────


@cli.group(cls=_SortedHelp, help="CIH governance")
def cih() -> None:
    pass


@cih.command("register", help="Register a CIH governance project")
@click.argument("project_id")
@click.option("--spec", "-s", required=True, help="Project spec as JSON string or @file")
def cih_register(project_id: str, spec: str) -> None:
    registry = _get_registry()
    service = FAECLanguageReconstructionService(registry)
    spec_data = _load_json_arg(spec)
    result = service.approve_reconstruction_project(
        {
            "project_id": project_id,
            "spec": spec_data,
        }
    )
    click.echo(
        json.dumps(
            {
                "status": result.get("status"),
                "project_id": project_id,
                "trace_id": result.get("trace_id"),
                "certificate_id": result.get("certificate_id"),
            },
            indent=2,
        )
    )


@cih.command("approve", help="Approve a CIH project (submit final approval)")
@click.argument("project_id")
@click.option("--spec", help="Optional approval spec override as JSON or @file")
def cih_approve(project_id: str, spec: str | None) -> None:
    registry = _get_registry()
    service = FAECLanguageReconstructionService(registry)
    spec_data = _load_json_arg(spec) if spec else None
    result = service.approve_reconstruction_project(
        {
            "project_id": project_id,
            "spec": spec_data or {},
        }
    )
    click.echo(
        json.dumps(
            {
                "status": result.get("status"),
                "certificate_id": result.get("certificate_id"),
            },
            indent=2,
        )
    )


@cih.command("certificate", help="Get a sovereign certificate by ID")
@click.argument("certificate_id")
def cih_certificate(certificate_id: str) -> None:
    registry = _get_registry()
    service = FAECLanguageReconstructionService(registry)
    cert = service.get_certificate(certificate_id)
    if cert is None:
        click.echo(f"Certificate '{certificate_id}' not found", err=True)
        sys.exit(1)
    click.echo(json.dumps(cert, indent=2))


# ── reconstruct ─────────────────────────────────────────────────────


@cli.command(help="Run full FRA reconstruction pipeline")
@click.argument("corpus", default="ie")
@click.option("--evidence-ids", "-e", multiple=True, help="Specific evidence IDs (omit for all)")
@click.option(
    "--target", default="Proto-Indo-European", show_default=True, help="Target proto-language"
)
@click.option("--period", default="Classical→Modern", show_default=True, help="Time period")
@click.option("--cih/--no-cih", default=False, help="Run CIH approval after reconstruction")
@click.option(
    "--lineage/--no-lineage", default=False, help="Print attestation→certification lineage"
)
@click.option("--dantomax/--no-dantomax", default=False, help="Attach Dantomax attestation ledger")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output raw JSON")
def reconstruct(
    corpus: str,
    evidence_ids: tuple[str, ...],
    target: str,
    period: str,
    cih: bool,
    lineage: bool,
    dantomax: bool,
    json_output: bool,
) -> None:
    registry = _get_registry()
    ds = DantomaxClient() if dantomax else None
    if ds is not None:
        registry = EvidenceRegistry(dantomax_client=ds)

    seed_registry_from_corpus(registry, corpus)
    all_ids = list_evidence_ids(corpus)
    eids = list(evidence_ids) if evidence_ids else all_ids

    if not eids:
        click.echo("No evidence IDs available for this corpus", err=True)
        sys.exit(1)

    from ..ai.hlrm_agent import HLRMAIAgent

    agent = HLRMAIAgent(registry)
    engine = ChronologicalReconstruction(registry, agent, corpus_path=corpus)
    result = engine.reconstruct_language(target, period, eids)

    if json_output:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        status = result.get("status", "UNKNOWN")
        recon_id = result.get("reconstruction_id", "")
        proto = result.get("proto_form") or (result.get("proto_model") or {}).get(
            "primary", {}
        ).get("form", "?")
        rules = len(result.get("correspondence_search", {}).get("sound_changes", []))
        corr_sets = len(result.get("correspondence_search", {}).get("correspondence_sets", []))
        click.echo(f"Status: {status}")
        click.echo(f"ID:     {recon_id}")
        click.echo(f"Proto:  {proto}")
        click.echo(f"Correspondence sets: {corr_sets}  Rules: {rules}")

    if lineage:
        human = result.get("human_lineage") or ""
        if human:
            click.echo(f"\n{human}")

    if cih and result.get("status") == "COMPLETED":
        service = FAECLanguageReconstructionService(registry)
        approval = service.approve_reconstruction_project(
            {
                "project_id": f"proj_{corpus}_recon",
                "spec": {
                    "target_language": target,
                    "time_period": period,
                    "reconstruction_id": recon_id,
                    "evidence_sources": eids,
                },
            }
        )
        click.echo(
            json.dumps(
                {
                    "cih_status": approval.get("status"),
                    "certificate_id": approval.get("certificate_id"),
                },
                indent=2,
            )
        )


# ── linguistics ─────────────────────────────────────────────────────


@cli.group(cls=_SortedHelp, help="Direct linguistics engine (no evidence pipeline)")
def linguistics() -> None:
    pass


@linguistics.command("reconstruct", help="Reconstruct proto-form from cognate sets directly")
@click.argument("forms_json", required=False)
@click.option(
    "--file",
    "-f",
    "forms_file",
    type=click.Path(exists=True, path_type=str),
    help="JSON file containing {lang: form} dict",
)
@click.option(
    "--branch", "-b", multiple=True, help="Language branches to expect (e.g. lat got ang)"
)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output full JSON")
def ling_reconstruct(
    forms_json: str | None, forms_file: str | None, _branch: tuple[str, ...], json_output: bool
) -> None:
    if forms_file:
        forms = json.loads(Path(forms_file).read_text(encoding="utf-8"))
    elif forms_json:
        try:
            forms = json.loads(forms_json)
        except json.JSONDecodeError:
            click.echo("Error: forms_json must be valid JSON", err=True)
            sys.exit(1)
    else:
        click.echo("Error: provide FORMS_JSON or --file", err=True)
        sys.exit(1)
    if not isinstance(forms, dict):
        click.echo("Error: must be a dict of {lang: form}", err=True)
        sys.exit(1)

    engine = CorrespondenceEngine()
    hyps = engine.reconstruct_set(forms)

    if json_output:
        click.echo(
            json.dumps(
                [
                    {
                        "proto_form": h.proto_form,
                        "confidence": h.confidence,
                        "regularity_score": h.regularity_score,
                        "correspondence_sets": h.correspondence_sets,
                        "sound_changes": h.sound_change_sequence,
                    }
                    for h in hyps
                ],
                indent=2,
            )
        )
    else:
        for h in hyps:
            p, c, r = h.proto_form, h.confidence, h.regularity_score
            click.echo(f"Proto: {p}  confidence={c:.3f}  regularity={r:.3f}")
            if h.competing_hypotheses:
                click.echo(
                    f"  Alternatives: {[c.get('form', '?') for c in h.competing_hypotheses[:3]]}"
                )


@linguistics.command("features", help="List all IPA segments with their features")
@click.option("--search", "-s", help="Filter segments by name or feature")
@click.option("--csv", is_flag=True, default=False, help="Output as CSV")
def ling_features(search: str | None, csv: bool) -> None:
    rows = []
    for sym, feats in sorted(
        FEATURES.items(),
        key=lambda kv: (not kv[1] & {"pulmonic", "ejective", "implosive", "click"}, kv[0]),
    ):
        if search and search.lower() not in sym.lower() and search.lower() not in " ".join(feats):
            continue
        rows.append((sym, " ".join(sorted(feats))))

    if csv:
        click.echo("symbol,features")
        for sym, feats in rows:
            click.echo(f"{sym},{feats}")
    else:
        for sym, feats in rows:
            click.echo(f"  {sym:6s}  {feats}")


# ── simulation ────────────────────────────────────────────────────


@cli.group(cls=_SortedHelp, help="Simulation engine for reconstruction evaluation")
def simulation() -> None:
    pass


@simulation.command("trial", help="Run a single simulation + reconstruction trial")
@click.option("--languages", "-L", default=3, type=int, help="Number of daughter languages")
@click.option("--depth", "-D", default=3, type=int, help="Time depth (iterations of change)")
@click.option("--shared", "-S", default=0.3, type=float, help="Ratio of shared changes")
@click.option("--proto", "-p", default=None, help="Known proto-form (random if omitted)")
@click.option("--changes", "-c", default=6, type=int, help="Number of sound changes to simulate")
@click.option("--seed", type=int, default=None, help="RNG seed")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output full JSON")
def sim_trial(
    languages: int,
    depth: int,
    shared: float,
    proto: str | None,
    changes: int,
    seed: int | None,
    json_output: bool,
) -> None:
    from ..simulation import run_trial as _run_trial

    trial = _run_trial(
        language_count=languages,
        time_depth=depth,
        shared_change_ratio=shared,
        proto_form=proto,
        num_changes=changes,
        seed=seed,
    )
    if json_output:
        import json as _json

        click.echo(
            _json.dumps(
                {
                    "true_proto": trial.true_proto,
                    "reconstructed": trial.reconstructed_proto,
                    "daughters": trial.daughter_forms,
                    "metrics": trial.metrics,
                },
                indent=2,
            )
        )
    else:
        click.echo(f"True proto:      {trial.true_proto}")
        click.echo(f"Reconstructed:   {trial.reconstructed_proto}")
        click.echo(f"Daughters:       {trial.daughter_forms}")
        click.echo(f"Edit accuracy:   {trial.metrics.get('edit_accuracy', 0):.3f}")
        click.echo(f"Feature-weighted:{trial.metrics.get('feature_weighted_accuracy', 0):.3f}")
        click.echo(f"Change F1:       {trial.metrics.get('change_f1', 0):.3f}")


@simulation.command("battery", help="Run a battery of trials across configs")
@click.option("--trials", "-n", default=20, type=int, help="Trials per config")
@click.option("--seed", type=int, default=42, help="RNG seed")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output full JSON")
def sim_battery(trials: int, seed: int, json_output: bool) -> None:
    from ..simulation import run_battery as _run_battery

    results = _run_battery(num_trials=trials, seed=seed)
    if json_output:
        import json as _json

        click.echo(
            _json.dumps(
                {
                    k: {
                        "language_count": r.language_count,
                        "time_depth": r.time_depth,
                        "avg_edit_accuracy": r.avg_edit_accuracy,
                        "avg_feature_weighted": r.avg_feature_weighted,
                        "avg_change_f1": r.avg_change_f1,
                    }
                    for k, r in results.items()
                },
                indent=2,
            )
        )
    else:
        click.echo(
            f"{'Config':>10s}  {'Lang':>4s}  {'Depth':>5s}  "
            f"{'EditAcc':>7s}  {'FeatAcc':>7s}  {'ChgF1':>6s}"
        )
        click.echo("-" * 55)
        for k in sorted(results.keys()):
            r = results[k]
            click.echo(
                f"{k:>10s}  {r.language_count:>4d}  {r.time_depth:>5d}  "
                f"{r.avg_edit_accuracy:>7.3f}  "
                f"{r.avg_feature_weighted:>7.3f}  {r.avg_change_f1:>6.3f}"
            )


@linguistics.command("tokenize", help="Tokenize an IPA string")
@click.argument("text")
def ling_tokenize(text: str) -> None:
    toks = tokenize(text)
    click.echo(f"Input:  {text}")
    click.echo(f"Tokens: {' '.join(t.symbol for t in toks)}")
    click.echo(f"Count:  {len(toks)}")


@linguistics.command("phylogeny", help="Build a phylogenetic tree from cognate forms")
@click.argument("forms_json", required=False)
@click.option(
    "--file",
    "-f",
    "forms_file",
    type=click.Path(exists=True, path_type=str),
    help="JSON file containing {lang: form} dict",
)
@click.option("--newick", is_flag=True, default=False, help="Output Newick format only")
def ling_phylogeny(forms_json: str | None, forms_file: str | None, newick: bool) -> None:
    if forms_file:
        import json as _json

        forms = _json.loads(Path(forms_file).read_text(encoding="utf-8"))
    elif forms_json:
        import json as _json

        try:
            forms = _json.loads(forms_json)
        except _json.JSONDecodeError:
            click.echo("Error: forms_json must be valid JSON", err=True)
            sys.exit(1)
    else:
        click.echo("Error: provide FORMS_JSON or --file", err=True)
        sys.exit(1)
    if not isinstance(forms, dict):
        click.echo("Error: must be a dict of {lang: form}", err=True)
        sys.exit(1)

    tree = build_phylogeny(forms)

    if newick:
        click.echo(tree.to_newick())
    else:
        click.echo("Distance matrix:")
        dists = compute_distance_matrix(forms)
        langs = sorted(set(k[0] for k in dists))
        header = "       " + "  ".join(f"{lg:>6s}" for lg in langs)
        click.echo(header)
        for la in langs:
            row = f"{la:>4s}  "
            for lb in langs:
                d = dists.get((la, lb), 0.0)
                row += f"{d:>6.3f}"
            click.echo(row)
        click.echo(f"\nNewick tree: {tree.to_newick()}")


# ── helpers ─────────────────────────────────────────────────────────


def _get_registry() -> EvidenceRegistry:
    return EvidenceRegistry()


def _get_cel() -> ConstitutionalEvidenceLedger:
    registry = _get_registry()
    cel = registry.cel
    if cel is None:
        click.echo("CEL not available (no Dantomax client configured)", err=True)
        sys.exit(1)
    return cel


def _load_json_arg(arg: str) -> dict:
    if arg.startswith("@"):
        path = Path(arg[1:])
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(arg)


if __name__ == "__main__":
    cli()
