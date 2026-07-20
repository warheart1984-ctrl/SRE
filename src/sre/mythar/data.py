"""Canonical Mythar Living Lexicon data (clusters 12–94) + optional JSON export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SRC = "Mythar Living Lexicon / Gap-Fill Draft"

ROOTS: list[tuple[str, str, str]] = [
    ("ma", "mother / existence / breath-base (formally anchored kinship root)", "kinship"),
    ("ta", "earth-mark / stand; also this / that (demonstrative)", "nature"),
    ("la", "light / open", "nature"),
    ("ka", "vital force / walk-base / elder-heat", "motion"),
    ("kra", "vital / life-force / power / strength", "abstract"),
    ("ro", "rest / peace / settle", "abstract"),
    ("ya", "divine / sacred", "abstract"),
    ("tila", "cycle / turn", "abstract"),
    ("ba", "power / strength (paired with pa)", "kinship"),
    ("tor", "gate / threshold / rocky peak", "nature"),
    ("pla", "plain / open land", "nature"),
    ("ve", "see / vision", "body"),
    ("pa", "father / power", "kinship"),
    ("ti", "child / small / sacred diminutive (size; cf. chi=child)", "kinship"),
    ("ne", "sibling / near / kin; also no / not (negation sense)", "kinship"),
    ("bro", "sibling / brother-sister class", "kinship"),
    ("te", "you (2sg address)", "kinship"),
    ("nu", "nose / smell / breath / ear / hear", "body"),
    ("mu", "mouth / speech aperture; also person / human-breath", "body"),
    ("si", "eye / see / light-of-sight", "body"),
    ("li", "tongue / speech / taste", "body"),
    ("to", "hand / take / give", "body"),
    ("be", "head / mind / top", "body"),
    ("pe", "foot / base / step / stand", "body"),
    ("kor", "heart / core (anatomical; cf. rama=feeling-heart)", "body"),
    ("bu", "come / go / move", "motion"),
    ("re", "flow / run / river", "motion"),
    ("le", "flow (soft) / glide", "motion"),
    ("ga", "walk / carry / hold", "motion"),
    ("wi", "know / wisdom", "abstract"),
    ("su", "good / sweet / life / sky-above (quality sense)", "abstract"),
    ("ni", "name / soul / spirit", "abstract"),
    ("wa", "water / flow", "nature"),
    ("hi", "tree / high / grow / wood", "nature"),
    ("bo", "earth / ground", "nature"),
    ("di", "child-sacred variant of ti", "kinship"),
    ("mi", "spirit-name variant of ni; also small / grain", "abstract"),
    ("vi", "wisdom-see / inner sight; also life / living", "abstract"),
    ("zu", "sweet-life variant of su", "abstract"),
    ("va", "water-flow variant of wa", "nature"),
    ("ki", "power / vital craft (ka/kra lighter); also high-grow", "abstract"),
    ("po", "earth variant of bo", "nature"),
    ("pu", "move variant of bu; also animal / creature", "motion"),
    ("yu", "grace / knowing-see glide (ya~wi~ve)", "abstract"),
    ("yo", "divine / sacred glide (ya~jor)", "abstract"),
    ("fu", "blessing / fortune", "abstract"),
    ("ua", "flow / existence", "abstract"),
    ("na", "name / spirit (ni-class)", "abstract"),
    ("ra", "proclaim / intensify / ground; also great / big (scale)", "abstract"),
    ("ara", "proclaim / ground / craft-ending", "abstract"),
    ("akra", "intensified kra — vital force / heart-core", "abstract"),
    ("lmakra", "illuminated mother-heart (la+ma+akra)", "abstract"),
    ("yuckara", "graceful knowing-heart (yu+ckara/kra+ara)", "abstract"),
    ("tiki", "small sacred power / pure vital spark (ti+ki)", "abstract"),
    ("yocfua", "divine blessing flow / blessed becoming (yo+cfua/fu+ua)", "abstract"),
    ("manalara", "proclaimed mother-light-name (ma+na+la+ra)", "abstract"),
    ("fi", "truth / sacred verity; fire / flame (elemental)", "abstract"),
    ("aka", "power / gate-force (ka intensified)", "abstract"),
    ("fa", "blessing-light glide (fu+la)", "abstract"),
    ("makra", "mother-heart / existence-vital force (ma+kra)", "abstract"),
    ("yufala", "motion blessing-light (yu+fa+la)", "abstract"),
    ("tina", "sacred child-name (ti+na)", "kinship"),
    ("rofua", "resting blessing-flow (ro+fu+ua)", "abstract"),
    ("yakora", "divine heart-craft (ya+kra+ara)", "abstract"),
    ("lamina", "light small-name (la+mi+na)", "abstract"),
    ("sufala", "good blessing-light (su+fa+la)", "abstract"),
    ("yotira", "motion force-child-proclaim (yo+ti+ra)", "abstract"),
    ("krafu", "vital-force blessing (kra+fu)", "abstract"),
    ("yumana", "divine existence-name (yu+ma+na)", "abstract"),
    ("lamara", "light-existence proclamation (la+ma+ra)", "abstract"),
    ("yufina", "divine blessing-truth-name (yu+fi+na)", "abstract"),
    ("toraka", "gate-power (tor+aka)", "nature"),
    ("mafira", "mother-truth proclamation (ma+fi+ra)", "kinship"),
    ("yukra", "divine knowing-heart (yu+kra)", "abstract"),
    ("tifala", "child blessing-light (ti+fa+la)", "abstract"),
    ("ramina", "proclaimed small-name (ra+mi+na)", "abstract"),
    ("yokra", "divine force-heart (yo+kra)", "abstract"),
    ("fukara", "blessing heart-craft (fu+kra+ara)", "abstract"),
    ("lamayu", "light-existence-divine (la+ma+yu)", "abstract"),
    ("tifura", "child blessing-proclamation (ti+fu+ra)", "abstract"),
    ("yokala", "divine force-time/light (yo+ka+la)", "abstract"),
    ("makora", "mother-heart proclamation (ma+kra+ra)", "abstract"),
    ("e", "emergence / becoming (prefix)", "abstract"),
    ("ebro", "emergence-carrier / birth-force (e+bro)", "abstract"),
    ("j", "affirmation / self (prefix)", "abstract"),
    ("jya", "divine-affirmed self-power (j+ya)", "abstract"),
    ("ja", "affirmation / self / yes", "abstract"),
    ("pi", "seed / point / spark", "abstract"),
    ("fo", "gather / collective / public", "nature"),
    ("kajya", "divine-affirmed power (ka+jya)", "abstract"),
    ("lapio", "light-seed place (la+pi+o)", "nature"),
    ("mufay", "mother-breath blessing in grace (mu+fa+y)", "abstract"),
    ("haf", "embrace / gather / protect", "abstract"),
    ("ca", "particle of being / spark-grain", "abstract"),
    ("plafo", "open plain gathering (pla+fo)", "nature"),
    ("micala", "spark-light essence (mi+ca+la)", "abstract"),
    ("haftar", "protective proclamation (haf+ta+ra)", "abstract"),
    ("qay", "rooted life / living force", "abstract"),
    ("bla", "open breath / broad flow (pla-soft)", "nature"),
    ("qaytra", "proclaimed living force (qay+tra)", "abstract"),
    ("blapa", "open protective flow (bla+pa)", "abstract"),
    ("torja", "affirmed threshold (tor+ja)", "nature"),
    ("por", "carry / bear / bring forth", "motion"),
    ("mor", "rise / grow / swell", "abstract"),
    ("porka", "carried power (por+ka)", "abstract"),
    ("yala", "divine light (ya+la)", "abstract"),
    ("morkfu", "rising blessed force (mor+kfu)", "abstract"),
    ("lu", "flow-light / present movement", "motion"),
    ("fro", "force-rest / power-peace (ka+ro)", "abstract"),
    ("fra", "proclamation glide (ra-soft)", "abstract"),
    ("kyo", "force-knowing / light-craft", "abstract"),
    ("yor", "force-divine / yo-force", "abstract"),
    ("klu", "existence-flow (ma+lu)", "abstract"),
    ("pra", "proclaim / intensify-good", "abstract"),
    ("pli", "open variant of pla", "nature"),
    ("fya", "grace-power (ka+ya)", "abstract"),
    ("lor", "light-protect (la+pa)", "abstract"),
    ("ku", "place-power / grounded force; also ear (nu-class)", "nature"),
    ("flu", "divine flow (ya+lu)", "abstract"),
    ("pta", "this-place / present ground", "abstract"),
    ("ru", "rest-flow (ro+lu); also blood / life-flow", "abstract"),
    ("pro", "bearing / proclaim forward", "abstract"),
    ("tik", "child-name sacred (ti+na lighter)", "kinship"),
    ("kru", "heart-force (kra glide)", "abstract"),
    ("lam", "light-mother (la+ma)", "abstract"),
    ("yafora", "motion gathering proclaimed (ya+fo+ra)", "abstract"),
    ("mikra", "small vital-heart (mi+kra)", "abstract"),
    ("talu", "this-flow / present-movement (ta+lu)", "motion"),
    ("plamu", "open-mother ground (pla+mu)", "nature"),
    ("yafika", "divine-truth-power (ya+fi+ka)", "abstract"),
    ("torla", "gate-light (tor+la)", "nature"),
    ("kafro", "power-rest / force-peace (ka+fro)", "abstract"),
    ("yami", "divine small-being (ya+mi)", "abstract"),
    ("supla", "good-open plain (su+pla)", "nature"),
    ("mufra", "mother-breath proclamation (mu+fra)", "abstract"),
    ("lakyo", "light-force-knowing (la+kyo)", "abstract"),
    ("tinara", "child-name proclaimed (ti+na+ra)", "kinship"),
    ("yorfa", "force-blessing (yor+fa)", "abstract"),
    ("maklu", "mother-existence-flow (ma+klu)", "abstract"),
    ("sipra", "good-proclaimed (si+pra)", "abstract"),
    ("plika", "open-power (pli+ka)", "abstract"),
    ("yofra", "divine-proclamation (yo+fra)", "abstract"),
    ("tamu", "this-mother (ta+mu)", "kinship"),
    ("kafya", "power-grace (ka+fya)", "abstract"),
    ("lorpa", "light-protect (lor+pa)", "abstract"),
    ("minu", "small-spirit (mi+nu)", "abstract"),
    ("yupra", "motion proclaimed (yu+pra)", "abstract"),
    ("silu", "good-flow-light (si+lu)", "abstract"),
    ("torfa", "gate-blessing (tor+fa)", "nature"),
    ("plaku", "open-power-place (pla+ku)", "nature"),
    ("morka", "rising power (mor+ka)", "abstract"),
    ("yaflu", "divine-flow (ya+flu)", "abstract"),
    ("sipta", "good-this (si+pta)", "abstract"),
    ("lakra", "light-heart (la+kra)", "abstract"),
    ("yomu", "motion-mother (yo+mu)", "abstract"),
    ("tafra", "this-proclaimed (ta+fra)", "abstract"),
    ("plina", "open-name (pli+na)", "abstract"),
    ("yofka", "divine-craft-power (yo+fi+ka)", "abstract"),
    ("maru", "mother-rest (ma+ru)", "abstract"),
    ("sipro", "good-bearing (si+pro)", "abstract"),
    ("mufya", "mother-grace (mu+fya)", "abstract"),
    ("plaro", "open-rest (pla+ro)", "nature"),
    ("tikna", "child-name (tik+na)", "kinship"),
    ("yokru", "divine-heart-force (yo+kru)", "abstract"),
    ("lamfa", "light-mother-blessing (lam+fa)", "abstract"),
    ("sipla", "good-open (si+pla)", "nature"),
    ("makyo", "mother-knowing (ma+kyo)", "abstract"),
    ("torlu", "gate-flow (tor+lu)", "nature"),
    # High-priority Proto-World gap-fill universals (proposal K)
    ("da", "father-strong / elder (pa-class)", "kinship"),
    ("hu", "person / human", "kinship"),
    ("am", "eat / consume", "motion"),
    ("no", "deep sleep / rest-depth (ro extension)", "abstract"),
    ("du", "bad / heavy / burden; also two / dual", "abstract"),
    ("me", "I (oblique / self)", "kinship"),
    ("mica", "one / single / unity particle", "abstract"),
    ("ska", "stone / rock", "nature"),
    ("ula", "sky / above (la+su extension)", "nature"),
    # Proposal L — social / body / action / nature / abstract / logic / spatial gaps
    ("chi", "child / youth (independent of ti=small)", "kinship"),
    ("loi", "friend / companion / ally", "kinship"),
    ("sha", "other / stranger / foreign", "kinship"),
    ("sa", "speech / say / mouth-speech", "body"),
    ("rama", "heart / feeling (ra+ma); also great-many", "body"),
    ("ko", "bone / structure", "body"),
    ("peh", "create / shape / make", "motion"),
    ("dak", "break / cut / destroy", "motion"),
    ("toh", "give (to-extension)", "motion"),
    ("tek", "take / seize", "motion"),
    ("nuka", "death / end (nu+ka)", "abstract"),
    ("sola", "sun / day", "nature"),
    ("luna", "moon / night", "nature"),
    ("fe", "air / wind", "nature"),
    ("krato", "mountain / great stone (kra+to)", "nature"),
    ("bura", "path / way (bu+ra)", "motion"),
    ("tem", "time / duration", "abstract"),
    ("reka", "change / shift (re+ka)", "abstract"),
    ("ver", "truth / real (cognitive register; cf. fi sacred-verity)", "abstract"),
    ("never", "false / not-true (ne+ver)", "abstract"),
    ("lo", "love / affection; also up / rise", "abstract"),
    ("dunu", "fear / heavy-hear (du+nu)", "abstract"),
    ("tima", "few / small-amount (ti+ma)", "abstract"),
    ("sura", "all / complete (su+ra)", "abstract"),
    ("nema", "none / no-life (ne+ma)", "abstract"),
    ("ke", "if / condition", "abstract"),
    ("in", "inside / within", "motion"),
    ("ex", "outside / beyond", "motion"),
    ("duta", "downward / heavy-foot (du+ta)", "motion"),
    ("neta", "near / close (ne+ta)", "motion"),
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

COMPOUND_CLUSTERS_BASE: list[dict[str, Any]] = [
    CLUSTER_47,
    CLUSTER_48,
    {
        "cluster_id": 49,
        "name": "Makra-yufala",
        "forms": ["makra", "yufala"],
        "phrase": "Makra yufala ro ya",
        "domain": "abstract",
        "interpretation": "Mother-heart in divine blessing-light (heart-axis blessing invocation)",
        "poetic": "Mother-heart in divine blessing-light.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_49",
        "compounds": ["Makra ro", "Yufala ya", "Makra yufala"],
        "morphemes": [
            {
                "form": "makra",
                "gloss": "existence-heart / mother-vital force",
                "parts": [
                    {"form": "ma", "from": ["ma"], "gloss": "mother / existence"},
                    {"form": "kra", "from": ["kra"], "gloss": "vital heart / life-force"},
                ],
            },
            {
                "form": "yufala",
                "gloss": "divine blessing-light",
                "parts": [
                    {"form": "yu", "from": ["yu", "ya"], "gloss": "divine / grace glide"},
                    {"form": "fa", "from": ["fa", "fu", "la"], "gloss": "blessing-light"},
                    {"form": "la", "from": ["la"], "gloss": "light / open"},
                ],
            },
        ],
        "reinforces": ["ma", "kra", "yu", "fa", "la"],
        "metadata": {
            "feeling": "heart-axis blessing invocation",
            "provenance_note": "Extends kra-axis (47) with blessing-light (fa) glide",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 49,
            "forms": ["makra", "yufala"],
        },
    },
    {
        "cluster_id": 50,
        "name": "Tina-rofua",
        "forms": ["tina", "rofua"],
        "phrase": "Tina rofua ro ya",
        "domain": "kinship",
        "interpretation": "The child-name rests in blessed flow (identity stabilization / soul-naming)",
        "poetic": "The child-name rests in blessed flow.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_50",
        "compounds": ["Tina na", "Rofua ro", "Tina rofua"],
        "morphemes": [
            {
                "form": "tina",
                "gloss": "sacred child-name",
                "parts": [
                    {"form": "ti", "from": ["ti"], "gloss": "child / sacred diminutive"},
                    {"form": "na", "from": ["na", "ni"], "gloss": "name / spirit"},
                ],
            },
            {
                "form": "rofua",
                "gloss": "resting blessing-flow",
                "parts": [
                    {"form": "ro", "from": ["ro"], "gloss": "rest / peace"},
                    {"form": "fu", "from": ["fu"], "gloss": "blessing"},
                    {"form": "ua", "from": ["ua"], "gloss": "flow / existence"},
                ],
            },
        ],
        "reinforces": ["ti", "na", "ro", "fu", "ua"],
        "metadata": {
            "feeling": "identity stabilization / soul-naming",
            "provenance_note": "Links child ti (48) with name na and rest ro",
            "kind": "cluster",
            "source": SRC,
            "domain": "kinship",
            "cluster_id": 50,
            "forms": ["tina", "rofua"],
        },
    },
    {
        "cluster_id": 51,
        "name": "Yakora-lamina",
        "forms": ["yakora", "lamina"],
        "phrase": "Yakora lamina ro ya",
        "domain": "abstract",
        "interpretation": "Divine heart-craft illuminates the small name (name-axis illumination)",
        "poetic": "Divine heart-craft illuminates the small name.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_51",
        "compounds": ["Yakora kra", "Lamina na", "Yakora lamina"],
        "morphemes": [
            {
                "form": "yakora",
                "gloss": "motion heart-craft / divine vital craft",
                "parts": [
                    {"form": "ya", "from": ["ya", "yo"], "gloss": "divine / sacred"},
                    {"form": "kra", "from": ["kra"], "gloss": "vital heart"},
                    {"form": "ara", "from": ["ara"], "gloss": "craft / proclaim"},
                ],
            },
            {
                "form": "lamina",
                "gloss": "light small-name",
                "parts": [
                    {"form": "la", "from": ["la"], "gloss": "light"},
                    {"form": "mi", "from": ["mi", "ni"], "gloss": "spirit-name"},
                    {"form": "na", "from": ["na"], "gloss": "name"},
                ],
            },
        ],
        "reinforces": ["ya", "kra", "la", "mi", "na"],
        "metadata": {
            "feeling": "name-axis illumination",
            "provenance_note": "Pairs divine craft (yakora) with illuminated naming (lamina)",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 51,
            "forms": ["yakora", "lamina"],
        },
    },
    {
        "cluster_id": 52,
        "name": "Sufala-yotira",
        "forms": ["sufala", "yotira"],
        "phrase": "Sufala yotira ro ya",
        "domain": "abstract",
        "interpretation": "Good blessing-light proclaims the divine child-force (soul-awakening / proclamation)",
        "poetic": "Good blessing-light proclaims the divine child-force.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_52",
        "compounds": ["Sufala la", "Yotira ti", "Sufala yotira"],
        "morphemes": [
            {
                "form": "sufala",
                "gloss": "good blessing-light",
                "parts": [
                    {"form": "su", "from": ["su"], "gloss": "good / sweet"},
                    {"form": "fa", "from": ["fa", "fu", "la"], "gloss": "blessing-light"},
                    {"form": "la", "from": ["la"], "gloss": "light"},
                ],
            },
            {
                "form": "yotira",
                "gloss": "divine force-child-proclamation",
                "parts": [
                    {"form": "yo", "from": ["yo", "ya"], "gloss": "divine glide"},
                    {"form": "ti", "from": ["ti"], "gloss": "child"},
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim / intensify"},
                ],
            },
        ],
        "reinforces": ["su", "fa", "la", "yo", "ti", "ra"],
        "metadata": {
            "feeling": "soul-awakening / proclamation",
            "provenance_note": "Blessing-light meets child-force proclamation",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 52,
            "forms": ["sufala", "yotira"],
        },
    },
    {
        "cluster_id": 53,
        "name": "Krafu-yumana",
        "forms": ["krafu", "yumana"],
        "phrase": "Krafu yumana ro ya",
        "domain": "abstract",
        "interpretation": "Blessed vital force names divine existence (heart-naming / soul-naming)",
        "poetic": "Blessed vital force names divine existence.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_53",
        "compounds": ["Krafu kra", "Yumana ma", "Krafu yumana"],
        "morphemes": [
            {
                "form": "krafu",
                "gloss": "vital-force blessing",
                "parts": [
                    {"form": "kra", "from": ["kra"], "gloss": "vital heart"},
                    {"form": "fu", "from": ["fu"], "gloss": "blessing"},
                ],
            },
            {
                "form": "yumana",
                "gloss": "motion existence-name / divine existence-name",
                "parts": [
                    {"form": "yu", "from": ["yu", "ya"], "gloss": "divine / grace"},
                    {"form": "ma", "from": ["ma"], "gloss": "existence / mother"},
                    {"form": "na", "from": ["na", "ni"], "gloss": "name / spirit"},
                ],
            },
        ],
        "reinforces": ["kra", "fu", "yu", "ma", "na"],
        "metadata": {
            "feeling": "heart-naming / soul-naming",
            "provenance_note": "Kra blessing names existence (ma+na)",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 53,
            "forms": ["krafu", "yumana"],
        },
    },
    {
        "cluster_id": 54,
        "name": "Lamara-yufina",
        "forms": ["lamara", "yufina"],
        "phrase": "Lamara yufina ro ya",
        "domain": "abstract",
        "interpretation": "Light-existence proclaims the divine blessed true name (truth-axis naming)",
        "poetic": "Light-existence proclaims the divine blessed true name.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_54",
        "compounds": ["Lamara la", "Yufina fi", "Lamara yufina"],
        "morphemes": [
            {
                "form": "lamara",
                "gloss": "light-existence proclamation",
                "parts": [
                    {"form": "la", "from": ["la"], "gloss": "light"},
                    {"form": "ma", "from": ["ma"], "gloss": "existence"},
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim"},
                ],
            },
            {
                "form": "yufina",
                "gloss": "divine blessing-truth-name",
                "parts": [
                    {"form": "yu", "from": ["yu", "ya"], "gloss": "divine"},
                    {"form": "fi", "from": ["fi"], "gloss": "truth"},
                    {"form": "na", "from": ["na", "ni"], "gloss": "name"},
                ],
            },
        ],
        "reinforces": ["la", "ma", "ra", "yu", "fi", "na"],
        "metadata": {
            "feeling": "truth-axis naming",
            "provenance_note": "Introduces fi (truth) into naming compounds",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 54,
            "forms": ["lamara", "yufina"],
        },
    },
    {
        "cluster_id": 55,
        "name": "Toraka-mafira",
        "forms": ["toraka", "mafira"],
        "phrase": "Toraka mafira ro ya",
        "domain": "nature",
        "interpretation": "The gate-power proclaims mother-truth (threshold / initiation cluster)",
        "poetic": "The gate-power proclaims mother-truth.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_55",
        "compounds": ["Toraka tor", "Mafira ma", "Toraka mafira"],
        "morphemes": [
            {
                "form": "toraka",
                "gloss": "gate-power",
                "parts": [
                    {"form": "tor", "from": ["tor"], "gloss": "gate / threshold"},
                    {"form": "aka", "from": ["aka", "ka"], "gloss": "power / vital force"},
                ],
            },
            {
                "form": "mafira",
                "gloss": "mother-truth proclamation",
                "parts": [
                    {"form": "ma", "from": ["ma"], "gloss": "mother / existence"},
                    {"form": "fi", "from": ["fi"], "gloss": "truth"},
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim"},
                ],
            },
        ],
        "reinforces": ["tor", "aka", "ma", "fi", "ra"],
        "metadata": {
            "feeling": "threshold / initiation",
            "provenance_note": "Gate tor + power aka at mother-truth threshold",
            "kind": "cluster",
            "source": SRC,
            "domain": "nature",
            "cluster_id": 55,
            "forms": ["toraka", "mafira"],
        },
    },
    {
        "cluster_id": 56,
        "name": "Yukra-tifala",
        "forms": ["yukra", "tifala"],
        "phrase": "Yukra tifala ro ya",
        "domain": "kinship",
        "interpretation": "The knowing-heart blesses the child-light (heart-child alignment)",
        "poetic": "The knowing-heart blesses the child-light.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_56",
        "compounds": ["Yukra kra", "Tifala ti", "Yukra tifala"],
        "morphemes": [
            {
                "form": "yukra",
                "gloss": "divine knowing-heart",
                "parts": [
                    {"form": "yu", "from": ["yu", "wi", "ve"], "gloss": "knowing / grace glide"},
                    {"form": "kra", "from": ["kra"], "gloss": "heart / vital force"},
                ],
            },
            {
                "form": "tifala",
                "gloss": "child blessing-light",
                "parts": [
                    {"form": "ti", "from": ["ti"], "gloss": "child"},
                    {"form": "fa", "from": ["fa", "fu", "la"], "gloss": "blessing-light"},
                    {"form": "la", "from": ["la"], "gloss": "light"},
                ],
            },
        ],
        "reinforces": ["yu", "kra", "ti", "fa", "la"],
        "metadata": {
            "feeling": "heart-child alignment",
            "provenance_note": "Aligns yu+kra heart-knowing with child blessing-light",
            "kind": "cluster",
            "source": SRC,
            "domain": "kinship",
            "cluster_id": 56,
            "forms": ["yukra", "tifala"],
        },
    },
    {
        "cluster_id": 57,
        "name": "Ramina-yokra",
        "forms": ["ramina", "yokra"],
        "phrase": "Ramina yokra ro ya",
        "domain": "abstract",
        "interpretation": "The proclaimed small-name meets the divine heart-force (identity-heart convergence)",
        "poetic": "The proclaimed small-name meets the divine heart-force.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_57",
        "compounds": ["Ramina na", "Yokra kra", "Ramina yokra"],
        "morphemes": [
            {
                "form": "ramina",
                "gloss": "proclaimed small-name",
                "parts": [
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim"},
                    {"form": "mi", "from": ["mi", "ni"], "gloss": "spirit-name"},
                    {"form": "na", "from": ["na"], "gloss": "name"},
                ],
            },
            {
                "form": "yokra",
                "gloss": "divine force-heart",
                "parts": [
                    {"form": "yo", "from": ["yo", "ya"], "gloss": "divine force"},
                    {"form": "kra", "from": ["kra"], "gloss": "heart / vital"},
                ],
            },
        ],
        "reinforces": ["ra", "mi", "na", "yo", "kra"],
        "metadata": {
            "feeling": "identity-heart convergence",
            "provenance_note": "Named spirit (ramina) converges with divine kra",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 57,
            "forms": ["ramina", "yokra"],
        },
    },
    {
        "cluster_id": 58,
        "name": "Fukara-lamayu",
        "forms": ["fukara", "lamayu"],
        "phrase": "Fukara lamayu ro ya",
        "domain": "abstract",
        "interpretation": "Blessing-heart-craft in light-existence-divine (blessing-axis expansion)",
        "poetic": "Blessing-heart-craft in light-existence-divine.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_58",
        "compounds": ["Fukara fu", "Lamayu la", "Fukara lamayu"],
        "morphemes": [
            {
                "form": "fukara",
                "gloss": "blessing-heart-craft",
                "parts": [
                    {"form": "fu", "from": ["fu"], "gloss": "blessing"},
                    {"form": "kra", "from": ["kra"], "gloss": "heart"},
                    {"form": "ara", "from": ["ara"], "gloss": "craft"},
                ],
            },
            {
                "form": "lamayu",
                "gloss": "light-existence-divine",
                "parts": [
                    {"form": "la", "from": ["la"], "gloss": "light"},
                    {"form": "ma", "from": ["ma"], "gloss": "existence"},
                    {"form": "yu", "from": ["yu", "ya"], "gloss": "divine / grace"},
                ],
            },
        ],
        "reinforces": ["fu", "kra", "la", "ma", "yu"],
        "metadata": {
            "feeling": "blessing-axis expansion",
            "provenance_note": "Expands fu+kra craft into la+ma+yu divine field",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 58,
            "forms": ["fukara", "lamayu"],
        },
    },
    {
        "cluster_id": 59,
        "name": "Tifura-yokala",
        "forms": ["tifura", "yokala"],
        "phrase": "Tifura yokala ro ya",
        "domain": "kinship",
        "interpretation": "The child-blessing is proclaimed in divine force-light (child-axis proclamation)",
        "poetic": "The child-blessing is proclaimed in divine force-light.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_59",
        "compounds": ["Tifura ti", "Yokala yo", "Tifura yokala"],
        "morphemes": [
            {
                "form": "tifura",
                "gloss": "child blessing-proclamation",
                "parts": [
                    {"form": "ti", "from": ["ti"], "gloss": "child"},
                    {"form": "fu", "from": ["fu"], "gloss": "blessing"},
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim"},
                ],
            },
            {
                "form": "yokala",
                "gloss": "divine force-time/light",
                "parts": [
                    {"form": "yo", "from": ["yo", "ya"], "gloss": "divine force"},
                    {"form": "ka", "from": ["ka", "kra"], "gloss": "vital / time-force"},
                    {"form": "la", "from": ["la"], "gloss": "light"},
                ],
            },
        ],
        "reinforces": ["ti", "fu", "ra", "yo", "ka", "la"],
        "metadata": {
            "feeling": "child-axis proclamation",
            "provenance_note": "Child blessing proclaimed in yo+ka+la force-light",
            "kind": "cluster",
            "source": SRC,
            "domain": "kinship",
            "cluster_id": 59,
            "forms": ["tifura", "yokala"],
        },
    },
    {
        "cluster_id": 60,
        "name": "Makora-yufina-ro",
        "forms": ["makora", "yufina", "ro"],
        "phrase": "Makora yufina ro",
        "domain": "abstract",
        "interpretation": (
            "The mother-heart proclaims the divine blessed true name in peace "
            "(completion / sealing formula)"
        ),
        "poetic": "The mother-heart proclaims the divine blessed true name in peace.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_60",
        "compounds": ["Makora ma", "Yufina fi", "Makora yufina ro"],
        "morphemes": [
            {
                "form": "makora",
                "gloss": "mother-heart proclamation",
                "parts": [
                    {"form": "ma", "from": ["ma"], "gloss": "mother / existence"},
                    {"form": "kra", "from": ["kra"], "gloss": "heart / vital"},
                    {"form": "ra", "from": ["ra"], "gloss": "proclaim"},
                ],
            },
            {
                "form": "yufina",
                "gloss": "motion blessing-truth-name / divine blessed true name",
                "parts": [
                    {"form": "yu", "from": ["yu", "ya"], "gloss": "motion / divine"},
                    {"form": "fi", "from": ["fi"], "gloss": "truth"},
                    {"form": "na", "from": ["na", "ni"], "gloss": "name"},
                ],
            },
            {
                "form": "ro",
                "gloss": "rest / peace / seal",
                "parts": [
                    {"form": "ro", "from": ["ro"], "gloss": "rest / peace / settle"},
                ],
            },
        ],
        "reinforces": ["ma", "kra", "ra", "yu", "fi", "na", "ro"],
        "metadata": {
            "feeling": "completion / sealing formula",
            "sealing_note": "Terminal ro closes the naming arc; ya omitted by design",
            "provenance_note": "Culminates clusters 49–59 naming and blessing axis",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 60,
            "forms": ["makora", "yufina", "ro"],
        },
    },
    {
        "cluster_id": 61,
        "name": "Ebro-la-kajya-lapio-mufay",
        "forms": ["ebro", "la", "kajya", "lapio", "mufay"],
        "phrase": "Ebro la kajya lapio mufay",
        "domain": "abstract",
        "interpretation": (
            "Emergent bearer of light, divine-affirmed power, seed-light place, "
            "mother-breath blessing (full emergence invocation line)"
        ),
        "poetic": (
            "The one who emerges bearing light, whose power is affirmed by the divine, "
            "whose light-seed rests in place, blessed by the mother's breath."
        ),
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_61",
        "compounds": ["Ebro bro", "Kajya ka", "Lapio la", "Mufay mu"],
        "morphemes": [
            {
                "form": "ebro",
                "gloss": "emergent bearing / birth-force / emergence-carrier",
                "parts": [
                    {"form": "e", "from": ["e"], "gloss": "emergence / becoming"},
                    {"form": "bro", "from": ["bro"], "gloss": "carry / bear / bring forth"},
                ],
            },
            {
                "form": "la",
                "gloss": "light / illumination / light-axis",
                "parts": [
                    {"form": "la", "from": ["la"], "gloss": "light / open / clarity"},
                ],
            },
            {
                "form": "kajya",
                "gloss": "power affirmed in divine grace / divine-affirmed force",
                "parts": [
                    {"form": "ka", "from": ["ka"], "gloss": "power / force"},
                    {"form": "jya", "from": ["jya", "j", "ya"], "gloss": "self affirmed in divine call"},
                ],
            },
            {
                "form": "lapio",
                "gloss": "light-seed place / point of illumination",
                "parts": [
                    {"form": "la", "from": ["la"], "gloss": "light"},
                    {"form": "pi", "from": ["pi", "pe"], "gloss": "seed / point / spark"},
                    {"form": "o", "from": ["o"], "gloss": "place / grounding vowel"},
                ],
            },
            {
                "form": "mufay",
                "gloss": "mother-breath blessing in grace / graceful giving from mother-root",
                "parts": [
                    {"form": "mu", "from": ["mu", "ma"], "gloss": "mother-breath / deep existence (ma-class)"},
                    {"form": "fa", "from": ["fa", "fu"], "gloss": "give / yield / blessing"},
                    {"form": "y", "from": ["y", "ya"], "gloss": "divine glide / grace marker"},
                ],
            },
        ],
        "reinforces": ["e", "bro", "la", "ka", "ya", "pi", "mu", "fa"],
        "metadata": {
            "feeling": "emergence / full ritual invocation line",
            "axes": "emergence · light · divine-power · light-seed · mother-blessing",
            "provenance_note": "Five-syllable ritual line; parallels kra clusters 47–48 breadth",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 61,
            "forms": ["ebro", "la", "kajya", "lapio", "mufay"],
        },
    },
    {
        "cluster_id": 62,
        "name": "Plafo-micala-haftar",
        "forms": ["plafo", "micala", "haftar"],
        "phrase": "Plafo micala haftar",
        "domain": "nature",
        "interpretation": (
            "Open plain gathers the spark-light essence, proclaimed in protective embrace "
            "(grounding invocation)"
        ),
        "poetic": "In the wide plain, the small light-being is proclaimed and protected.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_62",
        "compounds": ["Plafo pla", "Micala mi", "Haftar haf"],
        "morphemes": [
            {
                "form": "plafo",
                "gloss": "open gathering / plain-collective / wide-ground assembly",
                "parts": [
                    {"form": "pla", "from": ["pla"], "gloss": "flat / open / plain"},
                    {"form": "fo", "from": ["fo"], "gloss": "gather / collective / public"},
                ],
            },
            {
                "form": "micala",
                "gloss": "small being of light / spark-light essence",
                "parts": [
                    {"form": "mi", "from": ["mi", "ni"], "gloss": "small / spark / grain"},
                    {"form": "ca", "from": ["ca"], "gloss": "particle of being"},
                    {"form": "la", "from": ["la"], "gloss": "light / illumination"},
                ],
            },
            {
                "form": "haftar",
                "gloss": "protective proclamation / embraced truth-call",
                "parts": [
                    {"form": "haf", "from": ["haf"], "gloss": "embrace / gather / protect"},
                    {"form": "ta", "from": ["ta"], "gloss": "this / demonstrative"},
                    {"form": "r/ra", "from": ["ra"], "gloss": "proclamation / intensification"},
                ],
            },
        ],
        "reinforces": ["pla", "fo", "mi", "ca", "la", "haf", "ta", "ra"],
        "metadata": {
            "feeling": "grounding / land-light-proclamation",
            "axes": "open ground · spark-being-light · protective proclamation",
            "provenance_note": "Grounding-axis parallel to heart (47) and emergence (61)",
            "kind": "cluster",
            "source": SRC,
            "domain": "nature",
            "cluster_id": 62,
            "forms": ["plafo", "micala", "haftar"],
        },
    },
    {
        "cluster_id": 63,
        "name": "Qaytra-blapa-torja",
        "forms": ["qaytra", "blapa", "torja"],
        "phrase": "Qaytra blapa torja",
        "domain": "nature",
        "interpretation": (
            "Proclaimed living force, open protective flow, affirmed threshold "
            "(threshold invocation)"
        ),
        "poetic": "Life is proclaimed, protection flows wide, and the gate affirms the self.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_63",
        "compounds": ["Qaytra qay", "Blapa bla", "Torja tor"],
        "morphemes": [
            {
                "form": "qaytra",
                "gloss": "proclaimed living force / rooted life called forth",
                "parts": [
                    {"form": "qay", "from": ["qay"], "gloss": "rooted life / living force"},
                    {"form": "tra", "from": ["ta", "ra"], "gloss": "this proclaimed / demonstrative call"},
                ],
            },
            {
                "form": "blapa",
                "gloss": "open protective flow / broad guarding breath",
                "parts": [
                    {"form": "bla", "from": ["bla", "pla"], "gloss": "open breath / broad flow"},
                    {"form": "pa", "from": ["pa"], "gloss": "protect / feed / guard (nurturing)"},
                ],
            },
            {
                "form": "torja",
                "gloss": "affirmed threshold / gate that says yes",
                "parts": [
                    {"form": "tor", "from": ["tor"], "gloss": "gate / threshold"},
                    {"form": "ja", "from": ["ja", "j"], "gloss": "affirmation / self / yes"},
                ],
            },
        ],
        "reinforces": ["qay", "ta", "ra", "bla", "pa", "tor", "ja"],
        "metadata": {
            "feeling": "threshold / life-protection-gate",
            "axes": "rooted life · open protection · affirmed threshold",
            "provenance_note": "Threshold-axis; extends tor (cluster 55) with ja affirmation",
            "kind": "cluster",
            "source": SRC,
            "domain": "nature",
            "cluster_id": 63,
            "forms": ["qaytra", "blapa", "torja"],
        },
    },
    {
        "cluster_id": 64,
        "name": "Vi-porka-yala-morkfu",
        "forms": ["vi", "porka", "yala", "morkfu"],
        "phrase": "Vi porka yala morkfu",
        "domain": "abstract",
        "interpretation": (
            "Inner knowing carries power into divine light, where rising blessing grows "
            "(knowing-power-light-growth invocation)"
        ),
        "poetic": "Inner sight bears the force, divine light receives it, and blessed growth follows.",
        "source_reference": SRC,
        "evidence_id": "evid_myt_cluster_64",
        "compounds": ["Vi wi", "Porka por", "Yala ya", "Morkfu mor"],
        "morphemes": [
            {
                "form": "vi",
                "gloss": "inner knowing / subtle vision / gentle awareness",
                "parts": [
                    {"form": "vi", "from": ["vi", "wi", "ve"], "gloss": "inner sight / subtle knowing"},
                ],
            },
            {
                "form": "porka",
                "gloss": "carried power / borne force / forward-moving vitality",
                "parts": [
                    {"form": "por", "from": ["por", "bro", "ga"], "gloss": "carry / bear / bring forth"},
                    {"form": "ka", "from": ["ka"], "gloss": "power / vital force"},
                ],
            },
            {
                "form": "yala",
                "gloss": "divine light / grace-illumination",
                "parts": [
                    {"form": "ya", "from": ["ya", "yo"], "gloss": "divine call / grace"},
                    {"form": "la", "from": ["la"], "gloss": "light / illumination"},
                ],
            },
            {
                "form": "morkfu",
                "gloss": "rising blessed force / growing vital blessing",
                "parts": [
                    {"form": "mor", "from": ["mor", "hi"], "gloss": "rise / grow / swell"},
                    {"form": "kfu", "from": ["kra", "fu", "ka"], "gloss": "vital blessing fusion"},
                ],
            },
        ],
        "reinforces": ["vi", "por", "ka", "ya", "la", "mor", "fu"],
        "metadata": {
            "feeling": "knowing → power → divine light → blessing-growth",
            "axes": "inner knowing · carried power · divine light · rising blessing",
            "provenance_note": "Growth-axis culmination; vi particle + por/mor bearing roots",
            "kind": "cluster",
            "source": SRC,
            "domain": "abstract",
            "cluster_id": 64,
            "forms": ["vi", "porka", "yala", "morkfu"],
        },
    },
]


def _triad_cluster(
    cluster_id: int,
    forms: tuple[str, str, str],
    phrase: str,
    domain: str,
    interpretation: str,
    poetic: str,
    morpheme_specs: tuple[
        tuple[str, str, tuple[tuple[str, list[str], str], ...]],
        tuple[str, str, tuple[tuple[str, list[str], str], ...]],
        tuple[str, str, tuple[tuple[str, list[str], str], ...]],
    ],
    reinforces: list[str],
    feeling: str,
    provenance_note: str = "",
) -> dict[str, Any]:
    f1, f2, f3 = forms
    morphemes = [
        {
            "form": mf,
            "gloss": gloss,
            "parts": [{"form": part, "from": roots, "gloss": pgloss} for part, roots, pgloss in parts],
        }
        for mf, gloss, parts in morpheme_specs
    ]
    return {
        "cluster_id": cluster_id,
        "name": f"{f1.capitalize()}-{f2}-{f3}",
        "forms": list(forms),
        "phrase": phrase,
        "domain": domain,
        "interpretation": interpretation,
        "poetic": poetic,
        "source_reference": SRC,
        "evidence_id": f"evid_myt_cluster_{cluster_id}",
        "compounds": [f"{f1.capitalize()} {f1[:2]}", f"{f2.capitalize()} {f2[:2]}", f"{f1.capitalize()} {f2}"],
        "morphemes": morphemes,
        "reinforces": reinforces,
        "metadata": {
            "feeling": feeling,
            "provenance_note": provenance_note or f"Ritual triad cluster {cluster_id}",
            "kind": "cluster",
            "source": SRC,
            "domain": domain,
            "cluster_id": cluster_id,
            "forms": list(forms),
        },
    }


def _clusters_65_80() -> list[dict[str, Any]]:
    def p(part: str, roots: list[str], gloss: str) -> tuple[str, list[str], str]:
        return (part, roots, gloss)

    return [
    _triad_cluster(
      65, ("yafora", "mikra", "talu"), "Yafora mikra talu", "abstract",
      "Divine gathering proclaims the small heart in present flow",
      "Divine gathering proclaims the small heart in present flow.",
      (
        ("yafora", "divine gathering proclaimed", (p("ya", ["ya", "yo"], "divine"), p("fo", ["fo"], "gathering"), p("ra", ["ra"], "proclaimed"))),
        ("mikra", "small vital-heart", (p("mi", ["mi", "ni"], "small / spirit"), p("kra", ["kra"], "vital heart"))),
        ("talu", "this-flow / present-movement", (p("ta", ["ta"], "this / demonstrative"), p("lu", ["lu", "le"], "flow-light / movement"))),
      ),
      ["ya", "fo", "ra", "mi", "kra", "ta", "lu"], "gathering · small heart · present flow",
      "Opens extended ritual triad arc (65–80)",
    ),
    _triad_cluster(
      66, ("plamu", "yafika", "torla"), "Plamu yafika torla", "nature",
      "Mother-ground opens; divine truth-power enters the lighted gate",
      "Mother-ground opens, divine truth-power enters the lighted gate.",
      (
        ("plamu", "open-mother ground", (p("pla", ["pla", "pli"], "open plain"), p("mu", ["mu", "ma"], "mother-breath / ground"))),
        ("yafika", "divine-truth-power", (p("ya", ["ya"], "divine"), p("fi", ["fi"], "truth"), p("ka", ["ka"], "power"))),
        ("torla", "gate-light", (p("tor", ["tor"], "gate"), p("la", ["la"], "light"))),
      ),
      ["pla", "mu", "ya", "fi", "ka", "tor", "la"], "mother-ground · truth-power · gate-light",
    ),
    _triad_cluster(
      67, ("kafro", "yami", "supla"), "Kafro yami supla", "nature",
      "Power rests; the divine small-being stands on the good open plain",
      "Power rests; the divine small-being stands on the good open plain.",
      (
        ("kafro", "power-rest / force-peace", (p("ka", ["ka"], "power"), p("fro", ["fro", "ro"], "force-rest"))),
        ("yami", "divine small-being", (p("ya", ["ya", "yo"], "motion"), p("mi", ["mi"], "small being"))),
        ("supla", "good-open plain", (p("su", ["su"], "good"), p("pla", ["pla"], "open plain"))),
      ),
      ["ka", "fro", "ya", "mi", "su", "pla"], "power-rest · divine being · good plain",
    ),
    _triad_cluster(
      68, ("mufra", "lakyo", "tinara"), "Mufra lakyo tinara", "kinship",
      "Mother-breath proclaims light-knowing; the child-name is called forth",
      "Mother-breath proclaims light-knowing; the child-name is called forth.",
      (
        ("mufra", "mother-breath proclamation", (p("mu", ["mu", "ma"], "mother-breath"), p("fra", ["fra", "ra"], "proclamation"))),
        ("lakyo", "light-force-knowing", (p("la", ["la"], "light"), p("kyo", ["kyo", "ki", "wi"], "force-knowing"))),
        ("tinara", "child-name proclaimed", (p("ti", ["ti", "tik"], "child"), p("na", ["na", "ni"], "name"), p("ra", ["ra"], "proclaimed"))),
      ),
      ["mu", "fra", "la", "kyo", "ti", "na", "ra"], "mother-breath · light-knowing · child-name",
    ),
    _triad_cluster(
      69, ("yorfa", "maklu", "sipra"), "Yorfa maklu sipra", "abstract",
      "Blessed force flows from mother-existence; goodness is proclaimed",
      "Blessed force flows from mother-existence; goodness is proclaimed.",
      (
        ("yorfa", "force-blessing", (p("yor", ["yor", "yo", "ya"], "force-divine"), p("fa", ["fa", "fu"], "blessing"))),
        ("maklu", "mother-existence-flow", (p("ma", ["ma"], "mother"), p("klu", ["klu", "lu"], "existence-flow"))),
        ("sipra", "good-proclaimed", (p("si", ["si"], "good-see"), p("pra", ["pra", "ra"], "proclaimed"))),
      ),
      ["yor", "fa", "ma", "klu", "si", "pra"], "force-blessing · mother-flow · good proclaimed",
    ),
    _triad_cluster(
      70, ("plika", "yofra", "tamu"), "Plika yofra tamu", "nature",
      "Open power meets divine proclamation in the mother-this",
      "Open power meets divine proclamation in the mother-this.",
      (
        ("plika", "open-power", (p("pli", ["pli", "pla"], "open"), p("ka", ["ka"], "power"))),
        ("yofra", "divine-proclamation", (p("yo", ["yo", "ya"], "divine"), p("fra", ["fra", "ra"], "proclamation"))),
        ("tamu", "this-mother", (p("ta", ["ta"], "this"), p("mu", ["mu", "ma"], "mother"))),
      ),
      ["pli", "ka", "yo", "fra", "ta", "mu"], "open power · divine proclaim · this-mother",
    ),
    _triad_cluster(
      71, ("kafya", "lorpa", "minu"), "Kafya lorpa minu", "abstract",
      "Grace-power protects with light; the small spirit rises",
      "Grace-power protects with light; the small spirit rises.",
      (
        ("kafya", "power-grace", (p("ka", ["ka"], "power"), p("fya", ["fya", "ya"], "grace"))),
        ("lorpa", "light-protect", (p("lor", ["lor", "la"], "light"), p("pa", ["pa"], "protect"))),
        ("minu", "small-spirit", (p("mi", ["mi"], "small"), p("nu", ["nu", "ni"], "spirit / breath"))),
      ),
      ["ka", "fya", "lor", "pa", "mi", "nu"], "grace-power · light-protect · small spirit",
    ),
    _triad_cluster(
      72, ("yupra", "makra", "silu"), "Yupra makra silu", "abstract",
      "The divine proclaims the mother-heart; good light flows",
      "The divine proclaims the mother-heart; good light flows.",
      (
        ("yupra", "divine-proclaimed", (p("yu", ["yu", "ya"], "divine"), p("pra", ["pra", "ra"], "proclaimed"))),
        ("makra", "mother-heart", (p("ma", ["ma"], "mother"), p("kra", ["kra"], "heart"))),
        ("silu", "good-flow-light", (p("si", ["si", "su"], "good"), p("lu", ["lu", "la"], "flow-light"))),
      ),
      ["yu", "pra", "ma", "kra", "si", "lu"], "divine proclaim · mother-heart · good flow",
    ),
    _triad_cluster(
      73, ("torfa", "yami", "plaku"), "Torfa yami plaku", "nature",
      "The gate blesses the divine small-being in the open place of power",
      "The gate blesses the divine small-being in the open place of power.",
      (
        ("torfa", "gate-blessing", (p("tor", ["tor"], "gate"), p("fa", ["fa", "fu"], "blessing"))),
        ("yami", "motion small-being", (p("ya", ["ya"], "divine"), p("mi", ["mi"], "small being"))),
        ("plaku", "open-power-place", (p("pla", ["pla"], "open"), p("ku", ["ku", "ka"], "place-power"))),
      ),
      ["tor", "fa", "ya", "mi", "pla", "ku"], "gate-blessing · divine being · open power-place",
    ),
    _triad_cluster(
      74, ("morka", "yaflu", "sipta"), "Morka yaflu sipta", "abstract",
      "Rising power flows divinely; goodness is here",
      "Rising power flows divinely; goodness is here.",
      (
        ("morka", "rising power", (p("mor", ["mor"], "rise"), p("ka", ["ka"], "power"))),
        ("yaflu", "divine-flow", (p("ya", ["ya"], "divine"), p("flu", ["flu", "lu"], "flow"))),
        ("sipta", "good-this", (p("si", ["si", "su"], "good"), p("pta", ["pta", "ta"], "this-place"))),
      ),
      ["mor", "ka", "ya", "flu", "si", "pta"], "rising power · divine flow · good-this",
    ),
    _triad_cluster(
      75, ("lakra", "yomu", "tafra"), "Lakra yomu tafra", "abstract",
      "Light-heart meets divine-mother; this is proclaimed",
      "Light-heart meets divine-mother; this is proclaimed.",
      (
        ("lakra", "light-heart", (p("la", ["la"], "light"), p("kra", ["kra"], "heart"))),
        ("yomu", "divine-mother", (p("yo", ["yo", "ya"], "divine"), p("mu", ["mu", "ma"], "mother"))),
        ("tafra", "this-proclaimed", (p("ta", ["ta"], "this"), p("fra", ["fra", "ra"], "proclaimed"))),
      ),
      ["la", "kra", "yo", "mu", "ta", "fra"], "light-heart · divine-mother · this proclaimed",
    ),
    _triad_cluster(
      76, ("plina", "yofka", "maru"), "Plina yofka maru", "abstract",
      "The open name receives divine craft-power; mother rests",
      "The open name receives divine craft-power; mother rests.",
      (
        ("plina", "open-name", (p("pli", ["pli", "pla"], "open"), p("na", ["na", "ni"], "name"))),
        ("yofka", "divine-craft-power", (p("yo", ["yo"], "motion"), p("fi", ["fi"], "truth-craft"), p("ka", ["ka"], "power"))),
        ("maru", "mother-rest", (p("ma", ["ma"], "mother"), p("ru", ["ru", "ro"], "rest-flow"))),
      ),
      ["pli", "na", "yo", "fi", "ka", "ma", "ru"], "open name · divine craft · mother rest",
    ),
    _triad_cluster(
      77, ("kafro", "yala", "sipro"), "Kafro yala sipro", "abstract",
      "Power rests in divine light; goodness is carried forward",
      "Power rests in divine light; goodness is carried forward.",
      (
        ("kafro", "power-rest", (p("ka", ["ka"], "power"), p("fro", ["fro", "ro"], "rest"))),
        ("yala", "divine light", (p("ya", ["ya"], "motion"), p("la", ["la"], "light"))),
        ("sipro", "good-bearing", (p("si", ["si", "su"], "good"), p("pro", ["pro", "por"], "bearing"))),
      ),
      ["ka", "fro", "ya", "la", "si", "pro"], "power-rest · divine light · good bearing",
    ),
    _triad_cluster(
      78, ("mufya", "plaro", "tikna"), "Mufya plaro tikna", "kinship",
      "Mother-grace rests openly; the child-name emerges",
      "Mother-grace rests openly; the child-name emerges.",
      (
        ("mufya", "mother-grace", (p("mu", ["mu", "ma"], "mother"), p("fya", ["fya", "ya"], "grace"))),
        ("plaro", "open-rest", (p("pla", ["pla"], "open"), p("ro", ["ro"], "rest"))),
        ("tikna", "child-name", (p("tik", ["tik", "ti"], "child"), p("na", ["na"], "name"))),
      ),
      ["mu", "fya", "pla", "ro", "tik", "na"], "mother-grace · open rest · child-name",
    ),
    _triad_cluster(
      79, ("yokru", "lamfa", "sipla"), "Yokru lamfa sipla", "abstract",
      "Divine heart-force blesses the mother-light; goodness opens",
      "Divine heart-force blesses the mother-light; goodness opens.",
      (
        ("yokru", "divine-heart-force", (p("yo", ["yo"], "divine"), p("kru", ["kru", "kra"], "heart-force"))),
        ("lamfa", "light-mother-blessing", (p("lam", ["lam", "la", "ma"], "light-mother"), p("fa", ["fa", "fu"], "blessing"))),
        ("sipla", "good-open", (p("si", ["si", "su"], "good"), p("pla", ["pla"], "open"))),
      ),
      ["yo", "kru", "lam", "fa", "si", "pla"], "divine heart-force · mother-light bless · good open",
    ),
    _triad_cluster(
      80, ("makyo", "yupra", "torlu"), "Makyo yupra torlu", "abstract",
      "Mother-knowing is divinely proclaimed; the gate flows",
      "Mother-knowing is divinely proclaimed; the gate flows.",
      (
        ("makyo", "mother-knowing", (p("ma", ["ma"], "mother"), p("kyo", ["kyo", "wi"], "knowing-force"))),
        ("yupra", "divine-proclaimed", (p("yu", ["yu", "ya"], "divine"), p("pra", ["pra", "ra"], "proclaimed"))),
        ("torlu", "gate-flow", (p("tor", ["tor"], "gate"), p("lu", ["lu", "le"], "flow"))),
      ),
      ["ma", "kyo", "yu", "pra", "tor", "lu"], "mother-knowing · divine proclaim · gate flow",
      "Closes extended ritual triad arc (65–80)",
    ),
  ]


COMPOUND_CLUSTERS: list[dict[str, Any]] = COMPOUND_CLUSTERS_BASE + _clusters_65_80()

# Proposal K — Proto-World universal mini-clusters (append after compounds for ID order)
CLUSTERS_81_87: list[tuple[int, str, str, str, str, str]] = [
    (81, "pa ne ti", "Father-kin-child", "kinship", "Pa ne ti ro ya",
     "Father–kin–child: family core (order variant of cluster 12)"),
    (82, "si nu to", "Eye-ear-hand", "body", "Si nu to kra ro",
     "Eye–ear–hand: full perception triad (order variant of cluster 13)"),
    (83, "fi wa hi", "Fire-water-tree", "nature", "Fi wa hi kra la",
     "Fire–water–tree: elemental living triad"),
    (84, "wi du ro", "Know-bad-rest", "abstract", "Wi du ro ya",
     "Know the heavy/bad; rest in the divine (wisdom through challenge)"),
    (85, "su bu ya", "Good-move-divine", "motion", "Su bu ya kra",
     "The good moves toward the divine (blessed journey)"),
    (86, "be ni la", "Head-name-light", "abstract", "Be ni la ro ya",
     "Head–name–light: enlightened mind"),
    (87, "du kra ro", "Heavy-vital-rest", "abstract", "Du kra ro ya",
     "Heavy vital force settles (transforming burden)"),
]

# Proposal L — demonstration mini-clusters for new universal roots
CLUSTERS_88_94: list[tuple[int, str, str, str, str, str]] = [
    (88, "chi ma loi", "Child-mother-friend", "kinship", "Chi ma loi ro ya",
     "Child–mother–friend: social bond triad"),
    (89, "sa toh tek", "Speak-give-take", "motion", "Sa toh tek ya",
     "Speak–give–take: communicative exchange"),
    (90, "sola luna fe", "Sun-moon-wind", "nature", "Sola luna fe kra",
     "Sun–moon–wind: sky cycle"),
    (91, "tem reka lo", "Time-change-love", "abstract", "Tem reka lo ya",
     "Time–change–love: affective becoming"),
    (92, "in ex neta", "Inside-outside-near", "motion", "In ex neta ro",
     "Inside–outside–near: spatial field"),
    (93, "ver never ke", "Truth-false-if", "abstract", "Ver never ke ya",
     "Truth–falsehood–condition: logic triad"),
    (94, "rama ko ru", "Heart-bone-blood", "body", "Rama ko ru kra",
     "Feeling-heart–bone–blood: embodied life"),
]

INVOCATION = (
    "Ye kra ro ya\n"
    "Lmakra yuckara\n"
    "Tiki yocfua manalara\n"
    "Makra yufala\n"
    "Makora yufina ro\n"
    "Ebro la kajya lapio mufay\n"
    "Plafo micala haftar\n"
    "Qaytra blapa torja\n"
    "Vi porka yala morkfu\n"
    "Yafora mikra talu\n"
    "Makyo yupra torlu\n"
    "Pa ne ti\n"
    "Fi wa hi\n"
    "Su bu ya\n"
    "Du kra ro\n"
    "Chi ma loi\n"
    "Sola luna fe\n"
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
    {"mythar": "fi", "proto_world": "*h₁yes- / *weid-", "domain": "abstract", "note": "truth / verity"},
    {"mythar": "ebro", "proto_world": "*h₁egʰ- / *bʰer-", "domain": "abstract", "note": "emergence-carrier"},
    {"mythar": "pi", "proto_world": "*peh₂-", "domain": "abstract", "note": "seed / point / spark"},
    {"mythar": "qay", "proto_world": "*gʷeyh₃- / *kʷey-", "domain": "abstract", "note": "rooted life"},
    {"mythar": "por", "proto_world": "*bʰer- / *per-", "domain": "motion", "note": "carry / bear"},
    {"mythar": "mor", "proto_world": "*mer- / *men-", "domain": "abstract", "note": "rise / grow"},
    {"mythar": "da", "proto_world": "*da- / *tata", "domain": "kinship", "note": "father / elder"},
    {"mythar": "hu", "proto_world": "* hum- / *gʷm̥-", "domain": "kinship", "note": "person / human"},
    {"mythar": "am", "proto_world": "*h₁ed- / *am-", "domain": "motion", "note": "eat / consume"},
    {"mythar": "no", "proto_world": "*sneud- / *h₃er-", "domain": "abstract", "note": "deep sleep / rest"},
    {"mythar": "du", "proto_world": "*dweh₂- / *gʷreh₂-", "domain": "abstract", "note": "two / heavy / bad"},
    {"mythar": "me", "proto_world": "*me- / *h₁me-", "domain": "kinship", "note": "I (oblique)"},
    {"mythar": "mica", "proto_world": "*sem- / *oi-no-", "domain": "abstract", "note": "one / single"},
    {"mythar": "ska", "proto_world": "*h₂ek- / *ḱer-", "domain": "nature", "note": "stone / rock"},
    {"mythar": "ula", "proto_world": "*h₂ew- / *dyew-", "domain": "nature", "note": "sky / above"},
    {"mythar": "fi", "proto_world": "*peh₂wr̥ / *h₁yes-", "domain": "nature", "note": "fire / truth (polysemy)"},
    {"mythar": "chi", "proto_world": "*ǵenh₁- / *tek-", "domain": "kinship", "note": "child / youth"},
    {"mythar": "loi", "proto_world": "*leubh- / *priH-", "domain": "kinship", "note": "friend / love-ally"},
    {"mythar": "sha", "proto_world": "*alyo- / *gʰosti-", "domain": "kinship", "note": "other / stranger"},
    {"mythar": "sa", "proto_world": "*sekʷ- / *bʰeh₂-", "domain": "body", "note": "speak / say"},
    {"mythar": "rama", "proto_world": "*ḱerd- / *meǵh₂-", "domain": "body", "note": "feeling-heart / many"},
    {"mythar": "ko", "proto_world": "*ost- / *ḱost-", "domain": "body", "note": "bone"},
    {"mythar": "peh", "proto_world": "*kʷer- / *dʰeh₁-", "domain": "motion", "note": "make / create"},
    {"mythar": "dak", "proto_world": "*bʰreg- / *sek-", "domain": "motion", "note": "break / cut"},
    {"mythar": "toh", "proto_world": "*deh₃-", "domain": "motion", "note": "give"},
    {"mythar": "tek", "proto_world": "*gʰebʰ- / *h₁ep-", "domain": "motion", "note": "take"},
    {"mythar": "sola", "proto_world": "*sóh₂wl̥", "domain": "nature", "note": "sun"},
    {"mythar": "luna", "proto_world": "*mḗh₁n̥s / *leuk-", "domain": "nature", "note": "moon"},
    {"mythar": "fe", "proto_world": "*h₂weh₁-", "domain": "nature", "note": "wind / air"},
    {"mythar": "tem", "proto_world": "*temp- / *yeh₂-", "domain": "abstract", "note": "time"},
    {"mythar": "ver", "proto_world": "*weh₁-ro- / *h₁es-", "domain": "abstract", "note": "truth / real"},
    {"mythar": "lo", "proto_world": "*leubh- / *h₁el-", "domain": "abstract", "note": "love / up"},
    {"mythar": "ke", "proto_world": "*kʷe- / *ye-", "domain": "abstract", "note": "if / condition"},
    {"mythar": "in", "proto_world": "*h₁en-", "domain": "motion", "note": "inside"},
    {"mythar": "ex", "proto_world": "*h₁eǵʰs-", "domain": "motion", "note": "outside"},
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
    for cid, forms_s, name, domain, phrase, interp in CLUSTERS_81_87 + CLUSTERS_88_94:
        forms = forms_s.split()
        proposal = "K" if cid <= 87 else "L"
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
                "metadata": {
                    "kind": "cluster",
                    "source": SRC,
                    "domain": domain,
                    "cluster_id": cid,
                    "forms": forms,
                    "proposal": proposal,
                    "provenance_note": (
                        "Proto-World universal gap-fill mini-cluster"
                        if proposal == "K"
                        else "Proposal L universal-root demonstration cluster"
                    ),
                },
            }
        )

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
            "Mythar Living Lexicon — gap-fill clusters 12–94 with atomic roots, "
            "compounds, Proto-World universals (proposals K–L), and domain tags."
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
            "H": "Naming / blessing / sealing axis (makra–makora — clusters 49–60)",
            "I": "Ritual invocation lines (ebro…mufay — clusters 61–64)",
            "J": "Extended ritual triads (yafora…torlu — clusters 65–80)",
            "K": "Proto-World universal gaps (da/hu/am/no/du/me/mica/ska/ula — clusters 81–87)",
            "L": "Social/body/action/nature/abstract/logic/spatial roots — clusters 88–94",
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
