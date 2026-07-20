#!/usr/bin/env python3
"""Build ie_cognate_expanded_v01.json with embedded historical attestations."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ie_cognate_expanded_v01.json"

# Scholarly bibliography (shared sources)
SRC = {
    "fortson2010": {
        "source_id": "fortson2010",
        "source_title": "Indo-European Language and Culture: An Introduction",
        "source_author": "Benjamin W. Fortson IV",
        "publication_year": 2010,
        "edition": "2nd",
    },
    "beekes2011": {
        "source_id": "beekes2011",
        "source_title": "Comparative Indo-European Linguistics: An Introduction",
        "source_author": "Robert S. P. Beekes",
        "publication_year": 2011,
        "edition": "2nd",
    },
    "watkins2011": {
        "source_id": "watkins2011",
        "source_title": "The American Heritage Dictionary of Indo-European Roots",
        "source_author": "Calvert Watkins",
        "publication_year": 2011,
        "edition": "3rd",
    },
    "kluge2011": {
        "source_id": "kluge2011",
        "source_title": "Etymologisches Wörterbuch der deutschen Sprache",
        "source_author": "Friedrich Kluge / Elmar Seebold",
        "publication_year": 2011,
        "edition": "25th",
    },
    "matasovic2009": {
        "source_id": "matasovic2009",
        "source_title": "Etymological Dictionary of Proto-Celtic",
        "source_author": "Ranko Matasović",
        "publication_year": 2009,
        "edition": "1st",
    },
    "derksen2008": {
        "source_id": "derksen2008",
        "source_title": "Etymological Dictionary of the Slavic Inherited Lexicon",
        "source_author": "Rick Derksen",
        "publication_year": 2008,
        "edition": "1st",
    },
    "smoczynski2018": {
        "source_id": "smoczynski2018",
        "source_title": "Lithuanian Etymological Dictionary",
        "source_author": "Wojciech Smoczyński",
        "publication_year": 2018,
        "edition": "1st",
    },
    "kimball1999": {
        "source_id": "kimball1999",
        "source_title": "Hittite Historical Phonology",
        "source_author": "Sara E. Kimball",
        "publication_year": 1999,
        "edition": "1st",
    },
    "adams2013": {
        "source_id": "adams2013",
        "source_title": "A Dictionary of Tocharian B",
        "source_author": "Douglas Q. Adams",
        "publication_year": 2013,
        "edition": "2nd",
    },
}

LANGS = {
    "LAT": ("Latin", "Classical", "Italy", "1st c. BCE"),
    "GRC": ("Ancient Greek", "Classical Attic", "Athens", "5th–4th c. BCE"),
    "SKT": ("Sanskrit", "Vedic/Classical", "North India", "2nd–1st mill. BCE"),
    "GOT": ("Gothic", "Wulfila", "Balkans", "4th c. CE"),
    "SGA": ("Old Irish", "Old Irish", "Ireland", "8th–9th c. CE"),
    "CU": ("Old Church Slavonic", "Canonical OCS", "Bulgaria/Macedonia", "9th–10th c. CE"),
    "LIT": ("Lithuanian", "Modern standard (conservative)", "Lithuania", "attested modern; archaic retention"),
    "HIT": ("Hittite", "Empire period", "Hattusa", "2nd mill. BCE"),
    "TXB": ("Tocharian B", "Kuchean", "Tarim Basin", "5th–8th c. CE"),
    "PIE": ("Proto-Indo-European", "Reconstructed", "Pontic–Caspian (hyp.)", "c. 4000–2500 BCE"),
}


def att(
    *,
    lang: str,
    lemma: str,
    form: str,
    gloss: str,
    category: str,
    src_key: str,
    page: str,
    evidence_class: str = "directly_attested",
    notes: str = "",
    flags: list[str] | None = None,
    manuscript: str = "",
    manuscript_or_inscription: str = "",
    confidence: float = 0.95,
    original: str | None = None,
) -> dict:
    meta = SRC[src_key]
    name, period, geo, approx = LANGS[lang]
    aid = f"att_{lang.lower()}_{lemma}"
    return {
        "attestation_id": aid,
        "language": lang,
        "normalized_form": form.lower().replace("*", ""),
        "original_form": original or form,
        "gloss": gloss,
        "grammatical_category": category,
        **meta,
        "page_or_entry": page,
        "manuscript_or_inscription": manuscript_or_inscription or manuscript,
        "approximate_date": approx,
        "geographic_origin": geo,
        "confidence": confidence,
        "evidence_class": evidence_class,
        "notes": notes,
        "flags": flags or [],
    }


def item(
    eid: str,
    form: str,
    meaning: str,
    attestation: dict,
    *,
    etype: str = "lexical_item",
    extra_meta: dict | None = None,
) -> dict:
    meta = {
        "source": f"{attestation['source_author']} {attestation['publication_year']} / {attestation['page_or_entry']}",
        "attestation": attestation,
        "attestation_ids": [attestation["attestation_id"]],
        "flags": list(attestation.get("flags") or []),
        "evidence_class": attestation["evidence_class"],
    }
    if extra_meta:
        meta.update(extra_meta)
    return {
        "evidence_id": eid,
        "type": etype,
        "form": form,
        "meaning": meaning,
        "gloss": attestation["gloss"],
        "metadata": meta,
        "provenance_chain": [attestation["attestation_id"]],
        "constitutional_tags": ["FAC-E", "FRA", "DANTOMAX"],
    }


# (lemma, gloss, category, {lang: (form, src, page, kwargs)})
ENTRIES: list[tuple] = []


def add(lemma: str, gloss: str, category: str, forms: dict) -> None:
    ENTRIES.append((lemma, gloss, category, forms))


# --- Numbers 1–10 ---
add(
    "one",
    "one",
    "numeral",
    {
        "LAT": ("unus", "fortson2010", "§8.2 numerals", {}),
        "GRC": ("heis", "fortson2010", "§8.2 / εἷς", {"original": "εἷς", "notes": "masc. nom.; neut. hen"}),
        "SKT": ("eka", "fortson2010", "§8.2 / eka-", {}),
        "GOT": ("ains", "kluge2011", "eins / Goth. ains", {}),
        "SGA": ("oen", "matasovic2009", "*oinos > óen", {"original": "óen"}),
        "CU": ("jedinu", "derksen2008", "edinъ", {"original": "ѥдинъ", "notes": "OCS forms vary"}),
        "LIT": ("vienas", "smoczynski2018", "vienas", {}),
        "TXB": ("se", "adams2013", "ṣe / sas", {"original": "ṣe", "flags": ["uncertain"], "confidence": 0.7, "notes": "Toch. B ṣe 'one'"}),
        "PIE": ("oynos", "fortson2010", "*óynos", {"evidence_class": "scholarly_reconstruction", "original": "*óynos", "confidence": 0.85}),
    },
)
add(
    "two",
    "two",
    "numeral",
    {
        "LAT": ("duo", "fortson2010", "§8.2", {}),
        "GRC": ("duo", "fortson2010", "δύω", {"original": "δύω"}),
        "SKT": ("dva", "fortson2010", "dva-", {}),
        "GOT": ("twai", "kluge2011", "zwei / Goth. twai", {}),
        "SGA": ("dau", "matasovic2009", "dá / dáu", {"original": "dá"}),
        "CU": ("dva", "derksen2008", "dъva", {}),
        "LIT": ("du", "smoczynski2018", "du / du", {}),
        "HIT": ("da", "kimball1999", "dā- 'two'", {"flags": ["uncertain"], "confidence": 0.65}),
        "TXB": ("wu", "adams2013", "wu / wi", {}),
        "PIE": ("duwo", "fortson2010", "*dwóh₁", {"evidence_class": "scholarly_reconstruction", "original": "*dwóh₁", "confidence": 0.9}),
    },
)
add(
    "three",
    "three",
    "numeral",
    {
        "LAT": ("tres", "fortson2010", "§8.2", {"original": "trēs"}),
        "GRC": ("treis", "fortson2010", "τρεῖς", {"original": "τρεῖς"}),
        "SKT": ("trayas", "fortson2010", "tráyas", {}),
        "GOT": ("threis", "kluge2011", "drei / Goth. þreis", {"original": "þreis"}),
        "SGA": ("tri", "matasovic2009", "trí", {"original": "trí"}),
        "CU": ("trije", "derksen2008", "trьje", {}),
        "LIT": ("trys", "smoczynski2018", "trys", {}),
        "HIT": ("teri", "kimball1999", "tēri-", {"confidence": 0.75}),
        "TXB": ("trey", "adams2013", "trai", {}),
        "PIE": ("treyes", "fortson2010", "*tréyes", {"evidence_class": "scholarly_reconstruction", "original": "*tréyes", "confidence": 0.9}),
    },
)
add(
    "four",
    "four",
    "numeral",
    {
        "LAT": ("quattuor", "fortson2010", "§8.2", {}),
        "GRC": ("tettares", "fortson2010", "τέτταρες", {"original": "τέτταρες"}),
        "SKT": ("catvaras", "fortson2010", "catvā́ras", {"original": "catvāras"}),
        "GOT": ("fidwor", "kluge2011", "vier / Goth. fidwor", {"notes": "Grimm's law + irregular"}),
        "SGA": ("cethair", "matasovic2009", "cethair", {}),
        "CU": ("cetyre", "derksen2008", "četyre", {"original": "четыри"}),
        "LIT": ("keturi", "smoczynski2018", "keturì", {}),
        "PIE": ("kwetwor", "fortson2010", "*kʷetwóres", {"evidence_class": "scholarly_reconstruction", "original": "*kʷetwóres", "confidence": 0.88}),
    },
)
add(
    "five",
    "five",
    "numeral",
    {
        "LAT": ("quinque", "fortson2010", "§8.2", {"original": "quīnque"}),
        "GRC": ("pente", "fortson2010", "πέντε", {"original": "πέντε"}),
        "SKT": ("panca", "fortson2010", "páñca", {"original": "pañca"}),
        "GOT": ("fimf", "kluge2011", "fünf / Goth. fimf", {}),
        "SGA": ("coic", "matasovic2009", "cóic", {"original": "cóic"}),
        "CU": ("peti", "derksen2008", "pętь", {"original": "пѧть"}),
        "LIT": ("penki", "smoczynski2018", "penkì", {}),
        "TXB": ("pis", "adams2013", "piś", {"original": "piś"}),
        "PIE": ("penkwe", "fortson2010", "*pénkʷe", {"evidence_class": "scholarly_reconstruction", "original": "*pénkʷe", "confidence": 0.9}),
    },
)
add(
    "six",
    "six",
    "numeral",
    {
        "LAT": ("sex", "fortson2010", "§8.2", {}),
        "GRC": ("hex", "fortson2010", "ἕξ", {"original": "ἕξ"}),
        "SKT": ("sas", "fortson2010", "ṣáṣ", {"original": "ṣaṣ"}),
        "GOT": ("saihs", "kluge2011", "sechs / Goth. saihs", {}),
        "SGA": ("se", "matasovic2009", "sé", {"original": "sé"}),
        "CU": ("sesti", "derksen2008", "šestь", {}),
        "LIT": ("sesi", "smoczynski2018", "šešì", {"original": "šeši"}),
        "PIE": ("sweks", "fortson2010", "*swéḱs", {"evidence_class": "scholarly_reconstruction", "original": "*swéḱs", "confidence": 0.85}),
    },
)
add(
    "seven",
    "seven",
    "numeral",
    {
        "LAT": ("septem", "fortson2010", "§8.2", {}),
        "GRC": ("hepta", "fortson2010", "ἑπτά", {"original": "ἑπτά"}),
        "SKT": ("sapta", "fortson2010", "saptá", {}),
        "GOT": ("sibun", "kluge2011", "sieben / Goth. sibun", {}),
        "SGA": ("secht", "matasovic2009", "secht", {}),
        "CU": ("sedmi", "derksen2008", "sedmь", {}),
        "LIT": ("septyni", "smoczynski2018", "septynì", {}),
        "HIT": ("sipta", "kimball1999", "šiptam-", {"flags": ["uncertain"], "confidence": 0.6, "notes": "Anatolian numeral evidence sparse"}),
        "PIE": ("septm", "fortson2010", "*septḿ̥", {"evidence_class": "scholarly_reconstruction", "original": "*septḿ̥", "confidence": 0.9}),
    },
)
add(
    "eight",
    "eight",
    "numeral",
    {
        "LAT": ("octo", "fortson2010", "§8.2", {"original": "octō"}),
        "GRC": ("okto", "fortson2010", "ὀκτώ", {"original": "ὀκτώ"}),
        "SKT": ("asta", "fortson2010", "aṣṭá", {"original": "aṣṭa"}),
        "GOT": ("ahtau", "kluge2011", "acht / Goth. ahtau", {}),
        "SGA": ("ocht", "matasovic2009", "ocht", {}),
        "CU": ("osmi", "derksen2008", "osmь", {}),
        "LIT": ("astuoni", "smoczynski2018", "aštuonì", {"original": "aštuoni"}),
        "PIE": ("oktow", "fortson2010", "*oḱtṓw", {"evidence_class": "scholarly_reconstruction", "original": "*oḱtṓw", "confidence": 0.88}),
    },
)
add(
    "nine",
    "nine",
    "numeral",
    {
        "LAT": ("novem", "fortson2010", "§8.2", {}),
        "GRC": ("ennea", "fortson2010", "ἐννέα", {"original": "ἐννέα"}),
        "SKT": ("nava", "fortson2010", "náva", {}),
        "GOT": ("niun", "kluge2011", "neun / Goth. niun", {}),
        "SGA": ("noi", "matasovic2009", "noí", {"original": "noí"}),
        "CU": ("deveti", "derksen2008", "devętь", {"notes": "d- onset analogical to 'ten' in Balto-Slavic", "flags": ["analogy"]}),
        "LIT": ("devyni", "smoczynski2018", "devynì", {"flags": ["analogy"], "notes": "Balto-Slavic d- by analogy with 'ten'"}),
        "PIE": ("newn", "fortson2010", "*h₁néwn̥", {"evidence_class": "scholarly_reconstruction", "original": "*h₁néwn̥", "confidence": 0.85}),
    },
)
add(
    "ten",
    "ten",
    "numeral",
    {
        "LAT": ("decem", "fortson2010", "§8.2", {}),
        "GRC": ("deka", "fortson2010", "δέκα", {"original": "δέκα"}),
        "SKT": ("dasa", "fortson2010", "dáśa", {"original": "daśa"}),
        "GOT": ("taihun", "kluge2011", "zehn / Goth. taíhun", {}),
        "SGA": ("deich", "matasovic2009", "deich", {}),
        "CU": ("deseti", "derksen2008", "desętь", {}),
        "LIT": ("desimt", "smoczynski2018", "dêšimt", {"original": "dešimt"}),
        "TXB": ("sak", "adams2013", "śak", {"original": "śak"}),
        "PIE": ("dekm", "fortson2010", "*déḱm̥", {"evidence_class": "scholarly_reconstruction", "original": "*déḱm̥", "confidence": 0.9}),
    },
)

# --- Body parts ---
add(
    "eye",
    "eye",
    "noun",
    {
        "LAT": ("oculus", "beekes2011", "oculus", {"notes": "diminutive of *okʷ-"}),
        "GRC": ("osse", "beekes2011", "ὄσσε (dual)", {"original": "ὄσσε", "notes": "dual 'eyes'; ophthalmos is a different formation", "flags": ["uncertain"]}),
        "SKT": ("aksi", "beekes2011", "ákṣi", {"original": "akṣi"}),
        "GOT": ("augo", "kluge2011", "Auge / Goth. augō", {}),
        "CU": ("oko", "derksen2008", "oko", {}),
        "LIT": ("akis", "smoczynski2018", "akìs", {}),
        "HIT": ("sakuwa", "kimball1999", "šākuwa", {"original": "šākuwa", "flags": ["disputed"], "notes": "Hittite 'eye' etymology disputed vs *h₃ekʷ-", "confidence": 0.55}),
        "PIE": ("okw", "beekes2011", "*h₃ekʷ-", {"evidence_class": "scholarly_reconstruction", "original": "*h₃ekʷ-", "confidence": 0.9}),
    },
)
add(
    "ear",
    "ear",
    "noun",
    {
        "LAT": ("auris", "beekes2011", "auris", {}),
        "GRC": ("ous", "beekes2011", "οὖς", {"original": "οὖς"}),
        "GOT": ("auso", "kluge2011", "Ohr / Goth. ausō", {}),
        "CU": ("ucho", "derksen2008", "uxo", {"original": "ухо"}),
        "LIT": ("ausis", "smoczynski2018", "ausìs", {}),
        "PIE": ("hews", "beekes2011", "*h₂ews-", {"evidence_class": "scholarly_reconstruction", "original": "*h₂éws-", "confidence": 0.85}),
    },
)
add(
    "tooth",
    "tooth",
    "noun",
    {
        "LAT": ("dens", "fortson2010", "dēns", {}),
        "GRC": ("odon", "fortson2010", "ὀδών", {"original": "ὀδών"}),
        "SKT": ("dant", "fortson2010", "dánt-", {}),
        "GOT": ("tunthus", "kluge2011", "Zahn / Goth. tunþus", {"original": "tunþus"}),
        "SGA": ("det", "matasovic2009", "dét", {"original": "dét"}),
        "LIT": ("dantis", "smoczynski2018", "dantìs", {}),
        "PIE": ("hdont", "fortson2010", "*h₁dónt-", {"evidence_class": "scholarly_reconstruction", "original": "*h₁dónt-", "confidence": 0.9}),
    },
)
add(
    "tongue",
    "tongue",
    "noun",
    {
        "LAT": ("lingua", "beekes2011", "lingua", {"flags": ["analogy"], "notes": "from *dingua by dissimilation / folk etymology with lingō"}),
        "GRC": ("glotta", "beekes2011", "γλῶττα", {"original": "γλῶττα"}),
        "SKT": ("jihva", "beekes2011", "jihvā́", {"original": "jihvā"}),
        "GOT": ("tuggo", "kluge2011", "Zunge / Goth. tuggō", {}),
        "SGA": ("tengae", "matasovic2009", "tengae", {}),
        "CU": ("jezyku", "derksen2008", "językъ", {"original": "ѩзыкъ"}),
        "LIT": ("liezuvis", "smoczynski2018", "liežùvis", {"original": "liežuvis"}),
        "PIE": ("dnghu", "beekes2011", "*dn̥ǵʰwéh₂", {"evidence_class": "scholarly_reconstruction", "original": "*dn̥ǵʰwéh₂", "confidence": 0.8, "flags": ["uncertain"]}),
    },
)
add(
    "hand",
    "hand",
    "noun",
    {
        "LAT": ("manus", "beekes2011", "manus", {"flags": ["disputed"], "notes": "Latin manus not securely from *ǵʰes-r-", "confidence": 0.5}),
        "GRC": ("kheir", "beekes2011", "χείρ", {"original": "χείρ"}),
        "SKT": ("hasta", "beekes2011", "hásta-", {}),
        "GOT": ("handus", "kluge2011", "Hand / Goth. handus", {"flags": ["uncertain"], "notes": "Germanic hand not securely IE-matched", "confidence": 0.55}),
        "SGA": ("lam", "matasovic2009", "lám", {"original": "lám", "flags": ["uncertain"]}),
        "CU": ("ruka", "derksen2008", "rǫka", {"original": "рѫка"}),
        "LIT": ("ranka", "smoczynski2018", "rankà", {}),
        "PIE": ("ghesr", "beekes2011", "*ǵʰés-r-", {"evidence_class": "scholarly_reconstruction", "original": "*ǵʰés-r-", "confidence": 0.7, "flags": ["uncertain"], "notes": "Not all daughters listed are secure cognates"}),
    },
)
add(
    "knee",
    "knee",
    "noun",
    {
        "LAT": ("genu", "fortson2010", "genū", {"original": "genū"}),
        "GRC": ("gonu", "fortson2010", "γόνυ", {"original": "γόνυ"}),
        "SKT": ("janu", "fortson2010", "jā́nu", {"original": "jānu"}),
        "GOT": ("kniu", "kluge2011", "Knie / Goth. kniu", {}),
        "CU": ("koleno", "derksen2008", "kolěno", {"flags": ["uncertain"], "notes": "Slavic formation may not be direct *ǵónu reflex"}),
        "HIT": ("genu", "kimball1999", "gēnu", {}),
        "PIE": ("gonu", "fortson2010", "*ǵónu", {"evidence_class": "scholarly_reconstruction", "original": "*ǵónu", "confidence": 0.92}),
    },
)
add(
    "bone",
    "bone",
    "noun",
    {
        "LAT": ("os", "beekes2011", "os, ossis", {}),
        "GRC": ("osteon", "beekes2011", "ὀστέον", {"original": "ὀστέον"}),
        "SKT": ("asthi", "beekes2011", "ásthi", {}),
        "HIT": ("hastai", "kimball1999", "ḫastāi", {"original": "ḫastāi", "manuscript_or_inscription": "cuneiform"}),
        "PIE": ("host", "beekes2011", "*h₃ésth₁", {"evidence_class": "scholarly_reconstruction", "original": "*h₃ésth₁", "confidence": 0.9}),
    },
)
add(
    "blood",
    "blood",
    "noun",
    {
        "SKT": ("asrj", "beekes2011", "ásṛj-", {"original": "asṛj"}),
        "HIT": ("eshar", "kimball1999", "ēšḫar", {"original": "ēšḫar", "manuscript_or_inscription": "cuneiform"}),
        "LAT": ("sanguis", "beekes2011", "sanguis", {"flags": ["uncertain"], "notes": "Latin sanguis etymology uncertain; not secure *h₁ésh₂r̥ reflex", "confidence": 0.4}),
        "GRC": ("haima", "beekes2011", "αἷμα", {"original": "αἷμα", "flags": ["uncertain"], "notes": "Greek haîma not from *h₁ésh₂r̥", "confidence": 0.35}),
        "LIT": ("kraujas", "smoczynski2018", "kraũjas", {"flags": ["uncertain"], "confidence": 0.45}),
        "PIE": ("eshr", "beekes2011", "*h₁ésh₂r̥", {"evidence_class": "scholarly_reconstruction", "original": "*h₁ésh₂r̥", "confidence": 0.85, "notes": "Best preserved in Indo-Iranian and Anatolian"}),
    },
)
add(
    "head",
    "head",
    "noun",
    {
        "LAT": ("caput", "beekes2011", "caput", {"flags": ["uncertain"], "notes": "caput vs *ḱap- debated", "confidence": 0.6}),
        "GRC": ("kephale", "beekes2011", "κεφαλή", {"original": "κεφαλή", "flags": ["uncertain"]}),
        "SKT": ("siras", "beekes2011", "śíras-", {"original": "śiras"}),
        "GOT": ("haubith", "kluge2011", "Haupt / Goth. haubiþ", {"original": "haubiþ"}),
        "LIT": ("galva", "smoczynski2018", "galvà", {"flags": ["uncertain"]}),
        "PIE": ("kerh", "beekes2011", "*ḱérh₂-", {"evidence_class": "scholarly_reconstruction", "original": "*ḱérh₂-", "confidence": 0.65, "flags": ["uncertain"]}),
    },
)

# --- Core verbs ---
add(
    "be",
    "be / is",
    "verb",
    {
        "LAT": ("esse", "fortson2010", "esse / est", {}),
        "GRC": ("eimi", "fortson2010", "εἰμί", {"original": "εἰμί"}),
        "SKT": ("as", "fortson2010", "ás- / ásti", {}),
        "GOT": ("ist", "kluge2011", "ist / Goth. ist", {}),
        "SGA": ("is", "matasovic2009", "is", {}),
        "CU": ("jestu", "derksen2008", "jestъ", {"original": "ѥстъ"}),
        "LIT": ("esti", "smoczynski2018", "èsti", {}),
        "HIT": ("es", "kimball1999", "ēš-", {"original": "ēš-"}),
        "PIE": ("hes", "fortson2010", "*h₁es-", {"evidence_class": "scholarly_reconstruction", "original": "*h₁es-", "confidence": 0.95}),
    },
)
add(
    "bear",
    "bear / carry",
    "verb",
    {
        "LAT": ("fero", "fortson2010", "ferō", {"original": "ferō"}),
        "GRC": ("phero", "fortson2010", "φέρω", {"original": "φέρω"}),
        "SKT": ("bharati", "fortson2010", "bhárati", {}),
        "GOT": ("bairan", "kluge2011", "bear / Goth. bairan", {}),
        "SGA": ("berid", "matasovic2009", "berid", {}),
        "CU": ("bero", "derksen2008", "berǫ", {"original": "берѫ"}),
        "LIT": ("berti", "smoczynski2018", "bẽrti", {"notes": "Lith. ber̃ti 'strew' related; nešti is usual 'carry'"}),
        "PIE": ("bher", "fortson2010", "*bʰer-", {"evidence_class": "scholarly_reconstruction", "original": "*bʰer-", "confidence": 0.95}),
    },
)
add(
    "give",
    "give",
    "verb",
    {
        "LAT": ("dare", "fortson2010", "dō / dare", {}),
        "GRC": ("didomi", "fortson2010", "δίδωμι", {"original": "δίδωμι"}),
        "SKT": ("dadati", "fortson2010", "dádāti", {}),
        "SGA": ("dobeir", "matasovic2009", "do·beir", {"original": "do·beir", "notes": "compound with ber- 'carry'"}),
        "CU": ("dati", "derksen2008", "dati", {}),
        "LIT": ("duoti", "smoczynski2018", "dúoti", {}),
        "HIT": ("da", "kimball1999", "dā-", {}),
        "GOT": ("giban", "kluge2011", "geben / Goth. giban", {"flags": ["uncertain"], "notes": "Germanic 'give' not from *deh₃-", "confidence": 0.4}),
        "PIE": ("deh3", "fortson2010", "*deh₃-", {"evidence_class": "scholarly_reconstruction", "original": "*deh₃-", "confidence": 0.92}),
    },
)
add(
    "know",
    "know",
    "verb",
    {
        "LAT": ("gnoscere", "fortson2010", "(g)nōscō", {"original": "nōscō"}),
        "GRC": ("gignosko", "fortson2010", "γιγνώσκω", {"original": "γιγνώσκω"}),
        "SKT": ("janati", "fortson2010", "jā́nāti", {"original": "jānāti"}),
        "GOT": ("kunnan", "kluge2011", "can / Goth. kunnan", {}),
        "SGA": ("adgnin", "matasovic2009", "ad·gnin", {"original": "ad·gnin"}),
        "CU": ("znati", "derksen2008", "znati", {}),
        "LIT": ("zinoti", "smoczynski2018", "žinóti", {"original": "žinoti"}),
        "PIE": ("gneh3", "fortson2010", "*ǵneh₃-", {"evidence_class": "scholarly_reconstruction", "original": "*ǵneh₃-", "confidence": 0.9}),
    },
)
add(
    "see",
    "see",
    "verb",
    {
        "LAT": ("videre", "fortson2010", "videō", {"original": "videō"}),
        "GRC": ("eidon", "fortson2010", "εἶδον / *weyd-", {"original": "εἶδον"}),
        "SKT": ("veda", "fortson2010", "véda 'knows' < *weyd-", {"notes": "Perfect used as 'know'; paśyati is usual 'see'"}),
        "GOT": ("saihwan", "kluge2011", "sehen / Goth. saíƕan", {"flags": ["uncertain"], "notes": "Germanic see root distinct", "confidence": 0.45}),
        "LIT": ("veizdeti", "smoczynski2018", "véizdėti", {"original": "veizdėti"}),
        "PIE": ("weyd", "fortson2010", "*weyd-", {"evidence_class": "scholarly_reconstruction", "original": "*weyd-", "confidence": 0.9}),
    },
)
add(
    "hear",
    "hear",
    "verb",
    {
        "GRC": ("akouo", "beekes2011", "ἀκούω", {"original": "ἀκούω", "flags": ["uncertain"], "confidence": 0.5}),
        "SKT": ("srnoti", "beekes2011", "śṛṇóti", {"original": "śṛṇoti"}),
        "GOT": ("hausjan", "kluge2011", "hören / Goth. hausjan", {}),
        "LIT": ("girdeti", "smoczynski2018", "girdė́ti", {"original": "girdėti", "flags": ["uncertain"]}),
        "LAT": ("audire", "beekes2011", "audiō", {"flags": ["uncertain"], "notes": "Latin audiō etymology disputed", "confidence": 0.45}),
        "PIE": ("klew", "beekes2011", "*ḱlew-", {"evidence_class": "scholarly_reconstruction", "original": "*ḱlew-", "confidence": 0.75, "notes": "Best in Indo-Iranian; not all listed forms are secure"}),
    },
)
add(
    "eat",
    "eat",
    "verb",
    {
        "LAT": ("edere", "fortson2010", "edō", {"original": "edō"}),
        "GRC": ("edo", "fortson2010", "ἔδω", {"original": "ἔδω"}),
        "SKT": ("atti", "fortson2010", "átti", {}),
        "GOT": ("itan", "kluge2011", "essen / Goth. itan", {}),
        "SGA": ("ithid", "matasovic2009", "ithid", {}),
        "CU": ("jasti", "derksen2008", "jasti", {}),
        "LIT": ("esti", "smoczynski2018", "ė́sti", {"original": "ėsti", "notes": "ėsti 'devour'; valgyti is usual 'eat'"}),
        "HIT": ("et", "kimball1999", "et- / ēt-", {}),
        "PIE": ("hed", "fortson2010", "*h₁ed-", {"evidence_class": "scholarly_reconstruction", "original": "*h₁ed-", "confidence": 0.95}),
    },
)
add(
    "drink",
    "drink",
    "verb",
    {
        "LAT": ("bibere", "beekes2011", "bibō", {"original": "bibō", "notes": "reduplicated *pi-ph₃-"}),
        "GRC": ("pino", "beekes2011", "πίνω", {"original": "πίνω"}),
        "SKT": ("pibati", "beekes2011", "píbati", {}),
        "HIT": ("eku", "kimball1999", "eku- / aku-", {}),
        "GOT": ("drinkan", "kluge2011", "trinken / Goth. drigkan", {"flags": ["uncertain"], "notes": "Germanic drink not from *peh₃-", "confidence": 0.35}),
        "LIT": ("gerti", "smoczynski2018", "gérti", {"flags": ["uncertain"], "confidence": 0.5}),
        "PIE": ("peh3", "beekes2011", "*peh₃-", {"evidence_class": "scholarly_reconstruction", "original": "*peh₃-", "confidence": 0.88}),
    },
)
add(
    "come",
    "come",
    "verb",
    {
        "LAT": ("venire", "fortson2010", "veniō", {"original": "veniō"}),
        "GRC": ("baino", "fortson2010", "βαίνω", {"original": "βαίνω", "notes": "*gʷem-"}),
        "SKT": ("gam", "fortson2010", "gácchati / gam-", {}),
        "GOT": ("qiman", "kluge2011", "kommen / Goth. qiman", {}),
        "LIT": ("eiti", "smoczynski2018", "eĩti", {"notes": "'go'; ateĩti 'come'"}),
        "CU": ("iti", "derksen2008", "iti", {}),
        "PIE": ("gwem", "fortson2010", "*gʷem-", {"evidence_class": "scholarly_reconstruction", "original": "*gʷem-", "confidence": 0.9}),
    },
)
add(
    "stand",
    "stand",
    "verb",
    {
        "LAT": ("stare", "fortson2010", "stō", {"original": "stō"}),
        "GRC": ("histemi", "fortson2010", "ἵστημι", {"original": "ἵστημι"}),
        "SKT": ("tisthati", "fortson2010", "tíṣṭhati", {"original": "tiṣṭhati"}),
        "GOT": ("standan", "kluge2011", "stehen / Goth. standan", {}),
        "CU": ("stati", "derksen2008", "stati", {}),
        "LIT": ("stoveti", "smoczynski2018", "stovė́ti", {"original": "stovėti"}),
        "HIT": ("istant", "kimball1999", "ištant-", {"flags": ["uncertain"], "confidence": 0.6}),
        "PIE": ("steh2", "fortson2010", "*steh₂-", {"evidence_class": "scholarly_reconstruction", "original": "*steh₂-", "confidence": 0.95}),
    },
)

# Ambiguous set: father (secure) already in mini; add for expanded completeness
add(
    "father",
    "father",
    "noun",
    {
        "LAT": ("pater", "fortson2010", "§1.2 pater", {}),
        "GRC": ("pater", "fortson2010", "πατήρ", {"original": "πατήρ"}),
        "SKT": ("pitar", "fortson2010", "pitár-", {}),
        "GOT": ("fadar", "kluge2011", "Vater / Goth. fadar", {}),
        "SGA": ("athir", "matasovic2009", "athair", {"original": "athair"}),
        "CU": ("otici", "derksen2008", "otьcь", {"flags": ["uncertain"], "notes": "Slavic otьcь not transparent *ph₂tēr reflex", "confidence": 0.4}),
        "LIT": ("tevas", "smoczynski2018", "tė́vas", {"original": "tėvas", "flags": ["uncertain"], "notes": "Lith. tėvas not from *ph₂tēr", "confidence": 0.35}),
        "TXB": ("pacer", "adams2013", "pācer", {"original": "pācer"}),
        "PIE": ("phter", "fortson2010", "*ph₂tēr", {"evidence_class": "scholarly_reconstruction", "original": "*ph₂tēr", "confidence": 0.95}),
    },
)


def build() -> dict:
    by_lang: dict[str, list] = {code: [] for code in LANGS}
    rules = []
    for lemma, gloss, category, forms in ENTRIES:
        for lang, spec in forms.items():
            form, src, page, kwargs = spec
            a = att(
                lang=lang,
                lemma=lemma,
                form=form,
                gloss=gloss,
                category=category,
                src_key=src,
                page=page,
                **kwargs,
            )
            eid = f"evid_{lang.lower()}_{lemma}"
            etype = "reconstruction" if lang == "PIE" else "lexical_item"
            if lang == "PIE":
                # store as phonological_rule companion for some
                by_lang[lang].append(
                    item(eid, form if form.startswith("*") else f"*{form}", gloss, a, etype=etype)
                )
            else:
                by_lang[lang].append(item(eid, form, gloss, a, etype=etype))

    # A few explicit sound-change rules (attested scholarly)
    rule_specs = [
        ("evid_pie_rule_grimm", "PIE p t k → PGmc f þ x (Grimm's Law)", "kluge2011", "Grimm's Law"),
        ("evid_pie_rule_centum", "PIE ḱ → k (centum)", "fortson2010", "§3 centum/satem"),
        ("evid_pie_rule_satem", "PIE ḱ → ś/s (satem)", "fortson2010", "§3 centum/satem"),
    ]
    for eid, rule, src, page in rule_specs:
        a = att(
            lang="PIE",
            lemma=eid.replace("evid_pie_rule_", "rule_"),
            form="RULE",
            gloss=rule,
            category="phonological_rule",
            src_key=src,
            page=page,
            evidence_class="scholarly_reconstruction",
            confidence=0.9,
        )
        by_lang["PIE"].append(
            {
                "evidence_id": eid,
                "type": "phonological_rule",
                "rule": rule,
                "meaning": rule,
                "metadata": {
                    "source": f"{a['source_author']} {a['publication_year']}",
                    "attestation": a,
                    "attestation_ids": [a["attestation_id"]],
                    "evidence_class": a["evidence_class"],
                    "flags": [],
                },
                "provenance_chain": [a["attestation_id"]],
                "constitutional_tags": ["FAC-E", "FRA", "DANTOMAX"],
            }
        )

    languages = []
    for code, (name, period, _geo, _approx) in LANGS.items():
        if not by_lang[code]:
            continue
        languages.append(
            {
                "code": code,
                "name": name,
                "periods": [{"name": period, "evidence": by_lang[code]}],
            }
        )

    return {
        "corpus_id": "ie_cognate_expanded_v01",
        "description": (
            "Expanded Indo-European comparative mini-corpus: numbers 1–10, body parts, "
            "core verbs, across Latin, Greek, Sanskrit, Gothic, Old Irish, OCS, Lithuanian, "
            "Hittite, Tocharian B, plus scholarly PIE. Forms from published handbooks; "
            "uncertain/disputed/analogical/borrowed items flagged. Each item embeds a "
            "Dantomax-shaped HistoricalAttestation."
        ),
        "references": [f"{v['source_author']}. {v['publication_year']}. {v['source_title']}." for v in SRC.values()],
        "languages": languages,
    }


def main() -> None:
    data = build()
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(p["evidence"]) for lang in data["languages"] for p in lang["periods"])
    print(f"Wrote {OUT} with {n} evidence items across {len(data['languages'])} languages")


if __name__ == "__main__":
    main()
