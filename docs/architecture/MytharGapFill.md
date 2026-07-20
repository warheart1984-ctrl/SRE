# Mythar Gap-Fill Living Lexicon

Status: Living data (`data/mythar_lexicon_v01.json`) · Engine: `src/sre/mythar/lexicon.py`

## Philosophical note

Mythar gap-fill is **evidence-constrained invention**: new roots and clusters are admitted only as tagged drafts with FAC-E1 source refs (`Mythar Living Lexicon / Gap-Fill Draft`). They feed FRA / cognate analysis but remain distinguishable from external comparative corpora (IE mini-set).

## Proposals A–E

| Proposal | Focus |
|----------|--------|
| **A** | Kinship triad gaps (`pa` / `ma` / `ti` / `ne` / `bro`) |
| **B** | Body–sense inventory (`nu` / `mu` / `si` / `li` / `to` / `be` / `pe` / `kor`) |
| **C** | Motion verbs (`bu` / `re` / `le` / `ga`) |
| **D** | Knowing–spirit set (`wi` / `su` / `ni` / `ve`) |
| **F** | Kra-axis compounds (`lmakra` / `yuckara` — cluster 47) |
| **G** | Blessing / birth triad (`tiki` / `yocfua` / `manalara` — cluster 48) |

## Clusters 12–48

| ID | Forms | Domain | Phrase | Interpretation |
|----|-------|--------|--------|----------------|
| 12 | pa ti ne | kinship | Pa ti ne ro ya | Father–child–kin |
| 13 | nu si to | body | Nu si to kra ro | Breath–eye–hand |
| 14 | bu re ga | motion | Bu re ga ya | Move–flow–carry |
| 15 | wi su ni | abstract | Wi su ni ro ya | Know good spirit |
| 16 | wa hi bo | nature | Wa hi bo kra la | Water–tree–earth |
| 17 | pa ma ti | kinship | Pa ma ti ro ya | Father–mother–child |
| 18 | ne si pa | kinship | Ne si pa kra ro | Kin–see–father |
| 19 | bro ti ne | kinship | Bro ti ne ya | Sibling–child–kin |
| 20 | ya ne ma | kinship | Ya ne ma ro | Divine–kin–mother |
| 21 | te pa ro | kinship | Te pa ro ya | You–father–rest |
| 22 | ma bro ya | kinship | Ma bro ya kra | Mother–sibling–divine |
| 23 | mu nu si | body | Mu nu si ro | Mouth–breath–eye |
| 24 | li to be | body | Li to be ya | Tongue–hand–head |
| 25 | pe hi nu | body | Pe hi nu kra | Foot–high–breath |
| 26 | kor kra si | body | Kor kra si ro | Heart–vital–eye |
| 27 | wa mu ro | body | Wa mu ro ya | Water–mouth–rest |
| 28 | bo li ga | body | Bo li ga kra | Earth–tongue–carry |
| 29 | bu ga re | motion | Bu ga re ya | Come–carry–flow |
| 30 | le bu to | motion | Le bu to ro | Flow–come–hand |
| 31 | wi bu ya | motion | Wi bu ya kra | Know–come–divine |
| 32 | re ga kra | motion | Re ga kra ro | Flow–carry–vital |
| 33 | su bu ro | motion | Su bu ro ya | Good–come–rest |
| 34 | hi ga bo | motion | Hi ga bo kra | High–carry–earth |
| 35 | wi ni su | abstract | Wi ni su ro | Know–name–good |
| 36 | ve wi ro | abstract | Ve wi ro ya | See–know–rest |
| 37 | ni ya kra | abstract | Ni ya kra ro | Name–divine–vital |
| 38 | su ni ma | abstract | Su ni ma ya | Good–name–existence |
| 39 | ve ni ya | abstract | Ve ni ya kra | See–name–divine |
| 40 | wi su ni ya | abstract | Wi su ni ya ro | Know–good–name–divine |
| 41 | wa hi bo | nature | Wa hi bo kra la | Water–tree–earth (reinforce 16) |
| 42 | la wa re | nature | La wa re ya | Light–water–flow |
| 43 | bo hi la | nature | Bo hi la kra | Earth–high–light |
| 44 | wa bo nu | nature | Wa bo nu ro | Water–earth–breath |
| 45 | hi wa ga | nature | Hi wa ga ya | High–water–carry |
| 46 | la bo ro | nature | La bo ro kra | Light–earth–rest |
| **47** | **lmakra yuckara** | abstract | Lmakra yuckara ro ya | Illuminated mother-heart ↔ divine knowing-heart (kra axis) |
| **48** | **tiki yocfua manalara** | abstract | Tiki yocfua manalara ro ya | Pure sacred spark · divine blessing flow · proclaimed mother-light-name |

**Cluster count: 37** (IDs 12–48 inclusive).

### Cluster 47 morphology

| Form | Decomposition | Gloss |
|------|---------------|-------|
| lmakra | lm/lam (la+ma) + akra (intensified kra) | illuminated mother-heart / light-existence vital-heart |
| yuckara | yu + ckara/kra + ara | graceful knowing-heart / divine vital craft |

Compounds: `Lmakra`, `Yuckara`, `Lmakra ro`, `Yuckara wi`. Ritual (metadata only): `La-ma-kra yu-kara u̯edya`.

### Cluster 48 morphology

| Form | Decomposition | Gloss |
|------|---------------|-------|
| tiki | ti + ki | small sacred power / pure vital spark / child of heart-force |
| yocfua | yo + cfua/fu + ua | divine blessing flow / graceful fortune / blessed becoming |
| manalara | ma + na + la + ra | proclaimed mother-light-name / illuminated existence of named spirit |

Compounds: `Tiki kra`, `Yocfua ro`, `Manalara ya`. Ritual (metadata only): `Tiki yo-fua ma-na-la-ra`.

## Sample invocation

```
Ye kra ro ya
Lmakra yuckara
Tiki yocfua manalara
Wi su ni ve ro ya
```

## Engine API

```python
from sre.mythar import MytharLexicon

lex = MytharLexicon()
lex.cluster_ids()           # 12..48
lex.list_clusters()         # summaries (includes 47–48)
lex.gap_fill()              # domain coverage + proposals
lex.compare_proto_world()   # Mythar ↔ Proto-World table
lex.seed_registry(registry) # FAC-E seed into EvidenceRegistry (+ Dantomax if configured)
```

## Demo

```powershell
python scripts/generate_mythar_lexicon.py   # regenerate JSON if needed
python scripts/run_local.py --corpus mythar-lex --dantomax
pytest -q tests/test_mythar_lexicon.py
```
