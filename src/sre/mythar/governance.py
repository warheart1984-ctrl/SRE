"""CRA-aligned governance metadata for Mythar roots and clusters.

Maps LRL-INV-05 (lexicon entries must be evidence-tagged and lineage-anchored)
onto the CRA Justification Graph vs Evidence Graph split *as exported fields*:

- identity / justification_dependency → Justification Graph
- evidence_dependency / assurance_level / cel_lineage → Evidence Graph
- lifecycle_state / revision_history → Governance Layer (CIH lifecycle semantics)

Evidence today: static lexicon JSON keeps ``binding_status=deferred`` placeholders;
``MytharLexicon.seed_registry`` binds to CEL at runtime when Dantomax/CEL are attached.
Drive G: document JSON placeholders as deferred; seeded registry metadata as bound only
when CEL writes succeed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ..evidence.registry import EvidenceRegistry

AssuranceLevel = Literal["experimental", "candidate", "validated"]
LifecycleState = Literal["Draft", "Review", "Ratified", "Active"]
BindingStatus = Literal["bound", "deferred", "placeholder"]

ASSURANCE_LEVELS: tuple[str, ...] = ("experimental", "candidate", "validated")
LIFECYCLE_STATES: tuple[str, ...] = ("Draft", "Review", "Ratified", "Active")

CEL_CHARTER_REF = "docs/governance/CEL_Charter_v01.md"
CRA_REF = "docs/architecture/CRA_ReferenceArchitecture_v1.md"
LRL_INV_05 = "LRL-INV-05 — Lexicon governance"

# Proposal K atomic forms (Proto-World universals) — see data.ROOTS comment.
PROPOSAL_K_FORMS: frozenset[str] = frozenset(
    {"da", "hu", "am", "no", "du", "duma", "me", "mica", "ska", "ula"}
)

# Proposal L atomic forms (social/body/action/nature/logic/spatial gap-fill).
PROPOSAL_L_FORMS: frozenset[str] = frozenset(
    {
        "chi",
        "loi",
        "sha",
        "sa",
        "rama",
        "ko",
        "peh",
        "dak",
        "toh",
        "tek",
        "nuka",
        "sola",
        "luna",
        "fe",
        "krato",
        "bura",
        "tem",
        "reka",
        "ver",
        "never",
        "lo",
        "alo",
        "dunu",
        "tima",
        "sura",
        "nema",
        "ke",
        "in",
        "ex",
        "duta",
        "neta",
        "taga",
    }
)

# Forms created or re-scoped by PGC-5 in lexicon v1.3.
PGC_V13_SPLIT_FORMS: frozenset[str] = frozenset({"ska", "krato", "taga", "duma", "alo", "pe"})
PGC_V13_CORRECTED_FORMS: frozenset[str] = frozenset({"to", "ta", "du"})

PGC_V13_REVISIONS: dict[str, list[dict[str, str]]] = {
    "to": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Removed stone sense; agency axis only (hand / give-take)",
            "rationale": "PGC-5: stone ≠ agency; stone → ska / krato",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "ta": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Restricted to demonstrative (deixis); foot/stand relocated",
            "rationale": "PGC-5: foot/stand ≠ deixis; foot/stand → pe / taga",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "du": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Restricted to burden axis; dual sense relocated to duma",
            "rationale": "PGC-5: two ≠ burden; two → duma",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "ska": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Admitted as dedicated stone/rock root (former to-stone)",
            "rationale": "PGC-5 split from to",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "krato": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Admitted as mountain / great-stone (stone family with ska)",
            "rationale": "PGC-5 split companion for to-stone sense",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "taga": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Admitted as stand / grounded foot (former ta foot/stand)",
            "rationale": "PGC-5 split from ta",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "duma": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Admitted as two / dual (former du dual sense)",
            "rationale": "PGC-5 split from du",
            "refs": "PGC-5; Proposal M",
        }
    ],
    "alo": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Admitted as up / rise (split from lo love sense)",
            "rationale": "Register split: lo=love; alo=upward motion",
            "refs": "Proposal L/M; PGC axis hygiene",
        }
    ],
    "pe": [
        {
            "version": "1.3",
            "timestamp": "2026-07-20",
            "change": "Confirmed as foot / base / stand (absorbs former ta foot-sense)",
            "rationale": "PGC-5: grounding sense lives at pe (with taga)",
            "refs": "PGC-5; Proposal M",
        }
    ],
}


def bind_governance_records_to_cel(
    registry: EvidenceRegistry,
    records: list[tuple[str, dict[str, Any]]],
) -> dict[str, str]:
    """
    After FAC-E seed + CEL writes, set ``binding_status=bound`` on governance records.

    Returns mapping ``subject_id → cel_entry_id`` for entries successfully bound.
    """
    bound: dict[str, str] = {}
    for subject_id, governance in records:
        validation = registry.get_validation_report(subject_id)
        cel_entry_id: str | None = None
        if validation is not None:
            cel_meta = (validation.report or {}).get("cel") or {}
            raw_id = cel_meta.get("cel_entry_id")
            if isinstance(raw_id, str) and raw_id:
                cel_entry_id = raw_id
        if cel_entry_id is None and registry.cel is not None:
            for entry in registry.cel.query_by_subject(subject_id):
                if entry.entry_type.value == "evidence":
                    cel_entry_id = entry.cel_entry_id
                    break
        if not cel_entry_id:
            continue
        lineage = dict(governance.get("cel_lineage") or {})
        lineage.update(
            {
                "binding_status": "bound",
                "subject_id": subject_id,
                "cel_entry_id": cel_entry_id,
            }
        )
        governance = dict(governance)
        governance["cel_lineage"] = lineage
        registry.update_evidence_content(
            subject_id,
            {"metadata": {"cra_governance": governance}},
        )
        bound[subject_id] = cel_entry_id
    return bound


def cel_lineage_ref(
    *,
    subject_id: str,
    kind: str,
    binding_status: BindingStatus = "deferred",
    cel_entry_id: str | None = None,
) -> dict[str, Any]:
    """Build a CEL lineage reference (deferred until ledger write)."""
    return {
        "binding_status": binding_status,
        "subject_id": subject_id,
        "cel_entry_id": cel_entry_id,
        "entry_type_hint": "evidence",
        "charter_ref": CEL_CHARTER_REF,
        "bind_when": (
            "MytharLexicon.seed_registry → EvidenceRegistry / CEL.record_evidence "
            f"(subject_id={subject_id})"
        ),
        "kind": kind,
    }


def make_governance(
    *,
    identity: str,
    kind: Literal["root", "cluster"],
    justification_dependency: str,
    evidence_dependency: str,
    assurance_level: AssuranceLevel,
    lifecycle_state: LifecycleState,
    subject_id: str,
    cel_lineage: dict[str, Any] | None = None,
    revision_history: list[dict[str, str]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shared CRA governance record for a root or cluster."""
    if assurance_level not in ASSURANCE_LEVELS:
        raise ValueError(f"invalid assurance_level: {assurance_level}")
    if lifecycle_state not in LIFECYCLE_STATES:
        raise ValueError(f"invalid lifecycle_state: {lifecycle_state}")
    record: dict[str, Any] = {
        "identity": identity,
        "kind": kind,
        "justification_dependency": justification_dependency,
        "evidence_dependency": evidence_dependency,
        "assurance_level": assurance_level,
        "lifecycle_state": lifecycle_state,
        "cel_lineage": cel_lineage or cel_lineage_ref(subject_id=subject_id, kind=kind),
        "revision_history": list(revision_history or []),
        "cra_refs": {
            "architecture": CRA_REF,
            "lrl_invariant": LRL_INV_05,
            "graphs": {
                "justification": "identity + justification_dependency",
                "evidence": "evidence_dependency + assurance_level + cel_lineage",
            },
        },
    }
    if extra:
        record.update(extra)
    return record


def classify_root_governance(
    *,
    form: str,
    domain: str,
    evidence_id: str,
    polysemy: dict[str, Any] | None,
    proto_world_note: str | None,
) -> dict[str, Any]:
    """Derive CRA governance for a Mythar root from inventory class."""
    revisions = list(PGC_V13_REVISIONS.get(form, []))
    identity = f"mythar:root:{form}"

    def _with_pw(base: str) -> str:
        if proto_world_note:
            return f"{base} Comparative: {proto_world_note}."
        return base

    if polysemy and polysemy.get("status") == "stable":
        assurance: AssuranceLevel = "validated"
        lifecycle: LifecycleState = "Active"
        justification = (
            f"PGC-stable polysemy on axis '{polysemy.get('axis')}'; "
            f"justified under PGC-1..5 ({CRA_REF} Justification Graph)."
        )
        evidence = _with_pw(
            f"Axis test clusters {polysemy.get('test_clusters')}; "
            f"source={SRC_TAG}; polysemy status=stable."
        )
    elif form in PGC_V13_CORRECTED_FORMS or form in PGC_V13_SPLIT_FORMS:
        assurance = "validated"
        lifecycle = "Active"
        justification = (
            "PGC-5 correction / split admitted in lexicon v1.3; "
            "polysemy axis hygiene under Polysemy Governance Contract."
        )
        evidence = _with_pw(
            f"PGC corrections ledger; FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}."
        )
    elif form in PROPOSAL_K_FORMS or form in PROPOSAL_L_FORMS:
        assurance = "candidate"
        lifecycle = "Review"
        proposal = "K" if form in PROPOSAL_K_FORMS else "L"
        justification = (
            f"Proposal {proposal} gap-fill admission; "
            "justified as evidence-constrained invention pending ratification."
        )
        evidence = _with_pw(f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}.")
    else:
        # Core inventory (proposals A–J era) and compounds — validated Active.
        assurance = "validated"
        lifecycle = "Active"
        justification = (
            "Core Living Lexicon inventory (proposals A–J / compound morphology); "
            "constitutional domain coverage under LRL."
        )
        evidence = _with_pw(f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}.")

    extra: dict[str, Any] = {"domain": domain}
    if polysemy:
        extra["polysemy_status"] = polysemy.get("status")
        extra["polysemy_axis"] = polysemy.get("axis")

    return make_governance(
        identity=identity,
        kind="root",
        justification_dependency=justification,
        evidence_dependency=evidence,
        assurance_level=assurance,
        lifecycle_state=lifecycle,
        subject_id=evidence_id,
        revision_history=revisions,
        extra=extra,
    )


SRC_TAG = "Mythar Living Lexicon / Gap-Fill Draft"


def classify_cluster_governance(
    *,
    cluster_id: int,
    name: str,
    domain: str,
    evidence_id: str,
    proposal: str | None = None,
    provenance_note: str | None = None,
) -> dict[str, Any]:
    """Derive CRA governance for a Mythar cluster from ID / proposal class."""
    identity = f"mythar:cluster:{cluster_id:02d}"
    revisions: list[dict[str, str]] = []

    if cluster_id == 95 or proposal == "M":
        assurance: AssuranceLevel = "candidate"
        lifecycle: LifecycleState = "Review"
        justification = (
            "Proposal M — PGC correction / axis-validation cluster; "
            "justifies dual (duma) and related splits under PGC-5."
        )
        evidence = (
            f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}; "
            "links PGC corrections for to/ta/du."
        )
        revisions = [
            {
                "version": "1.3",
                "timestamp": "2026-07-20",
                "change": "Cluster 95 admitted for PGC axis validation (pu hu duma)",
                "rationale": "Demonstrate dual root duma after PGC-5 split from du",
                "refs": "PGC-5; Proposal M",
            }
        ]
    elif cluster_id >= 81 or proposal in {"K", "L"}:
        assurance = "candidate"
        lifecycle = "Review"
        prop = proposal or ("K" if cluster_id <= 87 else "L")
        justification = (
            f"Proposal {prop} gap-fill mini-cluster; "
            "evidence-constrained invention pending ratification."
        )
        evidence = f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}."
    elif cluster_id >= 47:
        assurance = "validated"
        lifecycle = "Active"
        justification = (
            "Compound / ritual cluster (proposals F–J); "
            "established Living Lexicon morphology under LRL."
        )
        evidence = f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}."
        if provenance_note:
            evidence += f" Provenance: {provenance_note}."
    else:
        assurance = "validated"
        lifecycle = "Active"
        justification = (
            "Core domain triad (proposals A–E); baseline Living Lexicon coverage clusters 12–46."
        )
        evidence = f"FAC-E1 source={SRC_TAG}; evidence_id={evidence_id}."

    return make_governance(
        identity=identity,
        kind="cluster",
        justification_dependency=justification,
        evidence_dependency=evidence,
        assurance_level=assurance,
        lifecycle_state=lifecycle,
        subject_id=evidence_id,
        revision_history=revisions,
        extra={
            "cluster_id": cluster_id,
            "name": name,
            "domain": domain,
            "proposal": proposal,
        },
    )


def lexicon_governance_model() -> dict[str, Any]:
    """Document-level CRA governance model + expansion freeze policy."""
    return {
        "schema": "mythar.cra_governance.v1",
        "cra_ref": CRA_REF,
        "lrl_invariant": LRL_INV_05,
        "cel_charter_ref": CEL_CHARTER_REF,
        "fields": [
            "identity",
            "justification_dependency",
            "evidence_dependency",
            "assurance_level",
            "lifecycle_state",
            "cel_lineage",
            "revision_history",
        ],
        "assurance_levels": list(ASSURANCE_LEVELS),
        "lifecycle_states": list(LIFECYCLE_STATES),
        "classification_defaults": {
            "core_clusters_12_46": {"assurance": "validated", "lifecycle": "Active"},
            "compound_ritual_47_80": {"assurance": "validated", "lifecycle": "Active"},
            "proposals_K_L_81_94": {"assurance": "candidate", "lifecycle": "Review"},
            "proposal_M_95": {"assurance": "candidate", "lifecycle": "Review"},
            "pgc_stable_polysemy": {"assurance": "validated", "lifecycle": "Active"},
            "pgc_v13_corrections": {"assurance": "validated", "lifecycle": "Active"},
        },
        "cel_binding": {
            "status": "bound_on_seed_when_cel_configured",
            "how_to_bind": (
                "MytharLexicon.seed_registry records FAC-E evidence to CEL when Dantomax "
                "is attached, then bind_governance_records_to_cel sets cel_lineage.cel_entry_id "
                "and binding_status=bound on seeded evidence metadata."
            ),
            "subject_id_pattern": {
                "root": "evid_myt_root_{form}",
                "cluster": "evid_myt_cluster_{id:02d}",
            },
        },
        "expansion_policy": {
            "status": "frozen",
            "priority": "documentation_conformance_tooling",
            "enforcement": "declarative_metadata_only",
            "note": (
                "Core lexicon expansion is declared frozen in document metadata. "
                "Prefer CRA/PGC conformance, documentation, and reproducibility "
                "tooling over admitting new roots or clusters. A CEL governance "
                "exception for thaw is policy intent — not a runtime admissions "
                "gate in the current Mythar modules (Drive-G-1)."
            ),
        },
    }


def validate_governance_record(record: dict[str, Any]) -> list[str]:
    """Return a list of validation errors (empty if ok)."""
    errors: list[str] = []
    required = (
        "identity",
        "justification_dependency",
        "evidence_dependency",
        "assurance_level",
        "lifecycle_state",
        "cel_lineage",
        "revision_history",
    )
    for key in required:
        if key not in record:
            errors.append(f"missing:{key}")
    level = record.get("assurance_level")
    if level is not None and level not in ASSURANCE_LEVELS:
        errors.append(f"assurance_level:{level}")
    state = record.get("lifecycle_state")
    if state is not None and state not in LIFECYCLE_STATES:
        errors.append(f"lifecycle_state:{state}")
    lineage = record.get("cel_lineage")
    if isinstance(lineage, dict):
        if not lineage.get("subject_id"):
            errors.append("cel_lineage.subject_id")
        if lineage.get("binding_status") not in ("bound", "deferred", "placeholder"):
            errors.append("cel_lineage.binding_status")
    else:
        errors.append("cel_lineage:type")
    if not isinstance(record.get("revision_history"), list):
        errors.append("revision_history:type")
    return errors
