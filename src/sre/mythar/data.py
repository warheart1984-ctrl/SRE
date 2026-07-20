"""Canonical Mythar Living Lexicon data (clusters 12–48) + optional JSON export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SRC = "Mythar Living Lexicon / Gap-Fill Draft"

ROOTS: list[tuple[str, str, str]] = [
    ("ma", "mother / existence / breath-base", "kinship"),
    ("ta", "earth-mark / stand", "nature"),
    ("la", "light / open", "nature"),
    ("ka", "vital force / walk-base", "motion"),
    ("kra", "vital / life-force", "abstract"),
    ("ro", "rest / peace / settle", "abstract"),
    ("ya", "divine / sacred", "abstract"),
    ("tila", "cycle / turn", "abstract"),
    ("ba", "power / strength (paired with pa)", "kinship"),
    ("tor", "gate / threshold", "nature"),
    ("pla", "plain / open land", "nature"),
    ("ve", "see / vision", "body"),
    ("pa", "father / power", "kinship"),
    ("ti", "child / small / sacred diminutive", "kinship"),
    ("ne", "sibling / near / kin", "kinship"),
    ("bro", "sibling / brother-sister class", "kinship"),
    ("te", "you (2sg address)", "kinship"),
    ("nu", "nose / smell / breath", "body"),
    ("mu", "mouth / speech aperture", "body"),
    ("si", "eye / see / light-of-sight", "body"),
    ("li", "tongue / speech / taste", "body"),
    ("to", "hand / take / give", "body"),
    ("be", "head / mind / top", "body"),
    ("pe", "foot / base / step", "body"),
    ("kor", "heart / core", "body"),
    ("bu", "come / go / move", "motion"),
    ("re", "flow / run / river", "motion"),
    ("le", "flow (soft) / glide", "motion"),
    ("ga", "walk / carry", "motion"),
    ("wi", "know / wisdom", "abstract"),
    ("su", "good / sweet / life", "abstract"),
    ("ni", "name / soul / spirit", "abstract"),
    ("wa", "water / flow", "nature"),
    ("hi", "tree / high / grow", "nature"),
    ("bo", "earth / ground", "nature"),
    ("di", "child-sacred variant of ti", "kinship"),
    ("mi", "spirit-name variant of ni", "abstract"),
    ("vi", "wisdom-see variant of wi/ve", "abstract"),
    ("zu", "sweet-life variant of su", "abstract"),
    ("va", "water-flow variant of wa", "nature"),
    ("ki", "power / vital craft (ka/kra lighter); also high-grow", "abstract"),
    ("po", "earth variant of bo", "nature"),
    ("pu", "move variant of bu", "motion"),
    ("yu", "grace / knowing-see glide (ya~wi~ve)", "abstract"),
    ("yo", "divine / sacred glide (ya~jor)", "abstract"),
    ("fu", "blessing / fortune", "abstract"),
    ("ua", "flow / existence", "abstract"),
    ("na", "name / spirit (ni-class)", "abstract"),
    ("ra", "proclaim / intensify / ground", "abstract"),
    ("ara", "proclaim / ground / craft-ending", "abstract"),
    ("akra", "intensified kra — vital force / heart-core", "abstract"),
    ("lmakra", "illuminated mother-heart (la+ma+akra)", "abstract"),
    ("yuckara", "graceful knowing-heart (yu+ckara/kra+ara)", "abstract"),
    ("tiki", "small sacred power / pure vital spark (ti+ki)", "abstract"),
    ("yocfua", "divine blessing flow / blessed becoming (yo+cfua/fu+ua)", "abstract"),
    ("manalara", "proclaimed mother-light-name (ma+na+la+ra)", "abstract"),
]

CLUSTERS: list[tuple[int, str, str, str, str, str]] = [
    (12, "pa ti ne", "Father-child-kin", "kinship", "Pa ti ne ro ya",
     "Father–child–kin triad; rest in the divine"),
    (13, "nu si to", "Breath-eye-hand", "body", "Nu si to kra ro",
     "Breath–sight–hand: vital perception and action at rest"),
    (14, "bu re ga", "Move-flow-carry", "motion", "Bu re ga ya",
     "Come–flow–carry toward the divine"),
    (15, "wi su ni", "Know good spirit", "abstract", "Wi su ni ro ya",
     "Know the good-named spirit; rest in the divine"),
    (16, "wa hi bo", "Water-tree-earth", "nature", "Wa hi bo kra la",
     "Water–tree–earth: living world under vital light"),
    (17, "pa ma ti", "Father-mother-child", "kinship", "Pa ma ti ro ya",
     "Core family triad settled in the divine"),
    (18, "ne si pa", "Kin-see-father", "kinship", "Ne si pa kra ro",
     "Kin sees the father: ancestral line of sight"),
    (19, "bro ti ne", "Sibling-child-kin", "kinship", "Bro ti ne ya",
     "Extended family: sibling–child–kin bond"),
    (20, "ya ne ma", "Divine-kin-mother", "kinship", "Ya ne ma ro",
     "Sacred ancestry through mother-kin"),
    (21, "te pa ro", "You-father-rest", "kinship", "Te pa ro ya",
     "Address to father in peace"),
    (22, "ma bro ya", "Mother-sibling-divine", "kinship", "Ma bro ya kra",
     "Maternal blessing over siblings"),
    (23, "mu nu si", "Mouth-breath-eye", "body", "Mu nu si ro",
     "Mouth–breath–eye: speech, breath, sight"),
    (24, "li to be", "Tongue-hand-head", "body", "Li to be ya",
     "Tongue–hand–head: speech, craft, mind"),
    (25, "pe hi nu", "Foot-high-breath", "body", "Pe hi nu kra",
     "Foot lifted; high breath — upright life"),
    (26, "kor kra si", "Heart-vital-eye", "body", "Kor kra si ro",
     "Heart’s vital eye: felt seeing"),
    (27, "wa mu ro", "Water-mouth-rest", "body", "Wa mu ro ya",
     "Water at the mouth; speech at rest"),
    (28, "bo li ga", "Earth-tongue-carry", "body", "Bo li ga kra",
     "Earth-tongue carries: grounded speech"),
    (29, "bu ga re", "Come-carry-flow", "motion", "Bu ga re ya",
     "Journey: come, carry, flow"),
    (30, "le bu to", "Flow-come-hand", "motion", "Le bu to ro",
     "Flow comes to the hand"),
    (31, "wi bu ya", "Know-come-divine", "motion", "Wi bu ya kra",
     "Knowledge comes to the divine"),
    (32, "re ga kra", "Flow-carry-vital", "motion", "Re ga kra ro",
     "Vital flow of carrying"),
    (33, "su bu ro", "Good-come-rest", "motion", "Su bu ro ya",
     "The good comes to rest"),
    (34, "hi ga bo", "High-carry-earth", "motion", "Hi ga bo kra",
     "Carry high upon the earth"),
    (35, "wi ni su", "Know-name-good", "abstract", "Wi ni su ro",
     "Know the good name"),
    (36, "ve wi ro", "See-know-rest", "abstract", "Ve wi ro ya",
     "See and know at rest"),
    (37, "ni ya kra", "Name-divine-vital", "abstract", "Ni ya kra ro",
     "Divine vital name"),
    (38, "su ni ma", "Good-name-existence", "abstract", "Su ni ma ya",
     "Good name of existence / mother-being"),
    (39, "ve ni ya", "See-name-divine", "abstract", "Ve ni ya kra",
     "See the divine name"),
    (40, "wi su ni ya", "Know-good-name-divine", "abstract", "Wi su ni ya ro",
     "Know the good divine name (four-morpheme seal)"),
    (41, "wa hi bo", "Water-tree-earth", "nature", "Wa hi bo kra la",
     "Reinforced living triad: water–tree–earth"),
    (42, "la wa re", "Light-water-flow", "nature", "La wa re ya",
     "Light upon flowing water"),
    (43, "bo hi la", "Earth-high-light", "nature", "Bo hi la kra",
     "Earth rises into high light"),
    (44, "wa bo nu", "Water-earth-breath", "nature", "Wa bo nu ro",
     "Water and earth breathe"),
    (45, "hi wa ga", "High-water-carry", "nature", "Hi wa ga ya",
     "High waters carry"),
    (46, "la bo ro", "Light-earth-rest", "nature", "La bo ro kra",
     "Light rests upon the earth"),
]

# Cluster 47 — compound kra-axis pair (structured beyond simple space-split roots)
CLUSTER_47: dict[str, Any] = {
    "cluster_id": 47,
    "name": "Lmakra-yuckara",
    "forms": ["lmakra", "yuckara"],
    "phrase": "Lmakra yuckara ro ya",
    "domain": "abstract",
    "interpretation": (
        "Call-and-response around kra: light-existence vital-heart — "
        "divine-knowing vital-craft (heart-activation / soul-alignment)"
    ),
    "poetic": "Light-existence vital-heart — divine-knowing vital-craft",
    "source_reference": SRC,
    "evidence_id": "evid_myt_cluster_47",
    "compounds": ["Lmakra", "Yuckara", "Lmakra ro", "Yuckara wi"],
    "morphemes": [
        {
            "form": "lmakra",
            "gloss": "illuminated mother-heart / light-existence vital-heart",
            "parts": [
                {"form": "lm/lam", "from": ["la", "ma"], "gloss": "light + existence/mother"},
                {"form": "akra", "from": ["akra", "kra"], "gloss": "intensified vital force / heart-core"},
            ],
        },
        {
            "form": "yuckara",
            "gloss": "graceful knowing-heart / divine vital craft",
            "parts": [
                {"form": "yu", "from": ["yu", "ya", "wi", "ve"], "gloss": "grace or know-see glide"},
                {"form": "ckara/kra", "from": ["kra"], "gloss": "vital heart"},
                {"form": "ara", "from": ["ara"], "gloss": "proclaim / ground / craft"},
            ],
        },
    ],
    "reinforces": ["la", "ma", "ya", "kra"],
    "metadata": {
        "feeling": "heart-activation / soul-alignment",
        "egyptian_ka_kra_note": (
            "Non-doctrinal resonance note: kra ~ Egyptian ka (vital essence) — "
            "comparative metaphor only, not constitutional evidence of descent"
        ),
        "gaulish_calibrated_ritual": "La-ma-kra yu-kara u̯edya",
        "provenance_note": "Links prior kra explorations (clusters 13, 15, 26, 32, 37)",
        "kind": "cluster",
        "source": SRC,
        "domain": "abstract",
        "cluster_id": 47,
        "forms": ["lmakra", "yuckara"],
    },
}

CLUSTER_48: dict[str, Any] = {
    "cluster_id": 48,
    "name": "Tiki-yocfua-manalara",
    "forms": ["tiki", "yocfua", "manalara"],
    "phrase": "Tiki yocfua manalara ro ya",
    "domain": "abstract",
    "interpretation": (
        "Three-part blessing / birth-awakening / soul emergence: "
        "pure sacred spark, divine blessed flow, proclaimed mother-light of the named spirit"
    ),
    "poetic": (
        "Pure sacred spark, divine blessed flow, "
        "proclaimed mother-light of the named spirit."
    ),
    "source_reference": SRC,
    "evidence_id": "evid_myt_cluster_48",
    "compounds": ["Tiki kra", "Yocfua ro", "Manalara ya"],
    "morphemes": [
        {
            "form": "tiki",
            "gloss": "small sacred power / pure vital spark / child of heart-force",
            "parts": [
                {"form": "ti", "from": ["ti"], "gloss": "small / sacred / child / pure"},
                {
                    "form": "ki",
                    "from": ["ki", "ka", "kra"],
                    "gloss": "power / vital craft (ka/kra lighter)",
                },
            ],
        },
        {
            "form": "yocfua",
            "gloss": "divine blessing flow / graceful fortune / blessed becoming",
            "parts": [
                {"form": "yo", "from": ["yo", "ya"], "gloss": "divine / sacred glide"},
                {"form": "cfua/fu", "from": ["fu"], "gloss": "blessing / fortune"},
                {"form": "ua", "from": ["ua"], "gloss": "flow / existence"},
            ],
        },
        {
            "form": "manalara",
            "gloss": "proclaimed mother-light-name / illuminated existence of named spirit",
            "parts": [
                {"form": "ma", "from": ["ma"], "gloss": "existence / mother"},
                {"form": "na", "from": ["na"], "gloss": "name / spirit"},
                {"form": "la", "from": ["la"], "gloss": "light"},
                {"form": "ra", "from": ["ra"], "gloss": "proclaim / intensify"},
            ],
        },
    ],
    "reinforces": ["ti", "ki", "ya", "ma", "la", "kra"],
    "metadata": {
        "feeling": "blessing / birth-awakening / soul emergence",
        "complements": "Complements kra clusters (47) with child + blessing dimensions",
        "ritual_string": "Tiki yo-fua ma-na-la-ra",
        "provenance_note": (
            "Links child/sacred ti (clusters 12, 17, 19) and kra-axis compounds (cluster 47)"
        ),
        "kind": "cluster",
        "source": SRC,
        "domain": "abstract",
        "cluster_id": 48,
        "forms": ["tiki", "yocfua", "manalara"],
    },
}

COMPOUND_CLUSTERS: list[dict[str, Any]] = [CLUSTER_47, CLUSTER_48]

INVOCATION = (
    "Ye kra ro ya\n"
    "Lmakra yuckara\n"
    "Tiki yocfua manalara\n"
    "Wi su ni ve ro ya"
)

PROTO_WORLD = [
    {"mythar": "pa", "proto_world": "*pa- / *baba", "domain": "kinship", "note": "father / parent"},
    {"mythar": "ma", "proto_world": "*ma- / *mama", "domain": "kinship", "note": "mother"},
    {"mythar": "ti", "proto_world": "*di- / *ti-", "domain": "kinship", "note": "child / small / pure"},
    {"mythar": "ne", "proto_world": "*na- / *ni-", "domain": "kinship", "note": "near / kin"},
    {"mythar": "bro", "proto_world": "*bʰréh₂tēr", "domain": "kinship", "note": "brother / sibling"},
    {"mythar": "nu", "proto_world": "*nu- / *sna-", "domain": "body", "note": "nose / breath"},
    {"mythar": "si", "proto_world": "*sekʷ- / *okʷ-", "domain": "body", "note": "see / eye"},
    {"mythar": "to", "proto_world": "*deh₃- / *tek-", "domain": "body", "note": "give / hand"},
    {"mythar": "kor", "proto_world": "*ḱerd-", "domain": "body", "note": "heart"},
    {"mythar": "bu", "proto_world": "*gʷem- / *bheu-", "domain": "motion", "note": "come / become"},
    {"mythar": "re", "proto_world": "*sreu- / *rei-", "domain": "motion", "note": "flow"},
    {"mythar": "wi", "proto_world": "*weid- / *ǵneh₃-", "domain": "abstract", "note": "know / see"},
    {"mythar": "su", "proto_world": "*su- / *swād-", "domain": "abstract", "note": "good / sweet"},
    {"mythar": "ni", "proto_world": "*h₁nómn̥ / *ane-", "domain": "abstract", "note": "name / breath-spirit"},
    {"mythar": "wa", "proto_world": "*wed- / *akʷ-", "domain": "nature", "note": "water"},
    {"mythar": "hi", "proto_world": "*ḱel- / *upér", "domain": "nature", "note": "high / cover"},
    {"mythar": "bo", "proto_world": "*dʰéǵʰōm / *bʰudʰ-", "domain": "nature", "note": "earth / ground"},
    {"mythar": "la", "proto_world": "*leuk-", "domain": "nature", "note": "light"},
    {"mythar": "kra", "proto_world": "*ḱerd- / ka", "domain": "abstract", "note": "vital heart / essence"},
    {"mythar": "yu", "proto_world": "*yu- / *yeu-", "domain": "abstract", "note": "join / grace glide"},
    {"mythar": "ara", "proto_world": "*h₂er- / *ar-", "domain": "abstract", "note": "fit / craft / ground"},
    {"mythar": "ki", "proto_world": "*ḱei- / *keh₂-", "domain": "abstract", "note": "vital craft / power"},
    {"mythar": "yo", "proto_world": "*yeu- / *dyew-", "domain": "abstract", "note": "divine glide"},
    {"mythar": "fu", "proto_world": "*bʰeh₂- / fortune calque", "domain": "abstract", "note": "blessing"},
    {"mythar": "ua", "proto_world": "*wed- / *h₂ew-", "domain": "abstract", "note": "flow / existence"},
    {"mythar": "na", "proto_world": "*h₁nómn̥", "domain": "abstract", "note": "name / spirit"},
    {"mythar": "ra", "proto_world": "*h₂er- / *reH-", "domain": "abstract", "note": "proclaim / intensify"},
]


def _is_compound_cluster(cluster: dict[str, Any]) -> bool:
    return bool(cluster.get("compounds"))


def build_lexicon_document() -> dict[str, Any]:
    gloss = {f: m for f, m, _ in ROOTS}
    roots = [
        {
            "form": form,
            "meaning": meaning,
            "domain": domain,
            "source_reference": SRC,
            "evidence_id": f"evid_myt_root_{form}",
        }
        for form, meaning, domain in ROOTS
    ]
    clusters: list[dict[str, Any]] = []
    for cid, forms_s, name, domain, phrase, interp in CLUSTERS:
        forms = forms_s.split()
        clusters.append(
            {
                "cluster_id": cid,
                "name": name,
                "forms": forms,
                "phrase": phrase,
                "domain": domain,
                "interpretation": interp,
                "source_reference": SRC,
                "evidence_id": f"evid_myt_cluster_{cid:02d}",
                "morphemes": [{"form": f, "gloss": gloss.get(f, f)} for f in forms],
            }
        )
    for compound in COMPOUND_CLUSTERS:
        clusters.append(dict(compound))

    evidence: list[dict[str, Any]] = []
    for r in roots:
        evidence.append(
            {
                "evidence_id": r["evidence_id"],
                "type": "lexical_item",
                "form": r["form"],
                "meaning": r["meaning"],
                "metadata": {"source": SRC, "domain": r["domain"], "kind": "root"},
            }
        )
    for c in clusters:
        meta: dict[str, Any] = {
            "source": SRC,
            "domain": c["domain"],
            "cluster_id": c["cluster_id"],
            "forms": c["forms"],
            "kind": "cluster",
        }
        if _is_compound_cluster(c):
            meta.update(c.get("metadata") or {})
            meta["compounds"] = c.get("compounds")
            meta["poetic"] = c.get("poetic")
            meta["reinforces"] = c.get("reinforces")
        evidence.append(
            {
                "evidence_id": c["evidence_id"],
                "type": "corpus_sample",
                "text": c["phrase"],
                "gloss": c["interpretation"],
                "metadata": meta,
            }
        )
        if _is_compound_cluster(c):
            for compound_form in c.get("compounds") or []:
                slug = compound_form.lower().replace(" ", "_")
                evidence.append(
                    {
                        "evidence_id": f"evid_myt_compound_{slug}",
                        "type": "lexical_item",
                        "form": compound_form,
                        "meaning": c["interpretation"],
                        "metadata": {
                            "source": SRC,
                            "domain": "abstract",
                            "kind": "compound",
                            "cluster_id": c["cluster_id"],
                            "provenance_note": meta.get("provenance_note"),
                        },
                    }
                )
    return {
        "lexicon_id": "mythar_lexicon_v01",
        "description": (
            "Mythar Living Lexicon — gap-fill clusters 12–48 with atomic roots, "
            "compounds (lmakra/yuckara; tiki/yocfua/manalara), domain tags, "
            "and Proto-World comparisons."
        ),
        "source_reference": SRC,
        "proposals": {
            "A": "Fill kinship triad gaps (pa/ma/ti/ne/bro)",
            "B": "Fill body–sense inventory (nu/mu/si/li/to/be/pe/kor)",
            "C": "Fill motion verbs (bu/re/le/ga)",
            "D": "Fill knowing–spirit set (wi/su/ni/ve)",
            "E": "Fill nature triad + light (wa/hi/bo/la)",
            "F": "Kra-axis compounds (lmakra / yuckara — cluster 47)",
            "G": "Blessing / birth triad (tiki / yocfua / manalara — cluster 48)",
        },
        "roots": roots,
        "clusters": clusters,
        "cluster_count": len(clusters),
        "root_count": len(roots),
        "invocation": INVOCATION,
        "proto_world_comparisons": PROTO_WORLD,
        "languages": [
            {
                "code": "MYT",
                "name": "Mythar",
                "periods": [{"name": "Living Lexicon", "evidence": evidence}],
            }
        ],
    }


def write_lexicon_json(path: Path | None = None) -> Path:
    out = path or DEFAULT_LEXICON_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = build_lexicon_document()
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


DEFAULT_LEXICON_PATH = Path(__file__).resolve().parents[3] / "data" / "mythar_lexicon_v01.json"
