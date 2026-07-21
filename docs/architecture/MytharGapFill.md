# Mythar Gap-Fill Living Lexicon

Status: Living data (`data/mythar_lexicon_v01.json`) · Engine: `src/sre/mythar/lexicon.py` · Governance: `src/sre/mythar/governance.py`  
**White paper (freeze synthesis):** [`MytharWhitePaper.md`](MytharWhitePaper.md)  
**Engine suite:** [`MytharEngineSuite.md`](MytharEngineSuite.md)  
**Drive G:** [`DriveG_DocumentationEvidenceLaw.md`](../governance/DriveG_DocumentationEvidenceLaw.md) — no claim may exceed implementation evidence

## Strategic posture (freeze)

**Core lexicon expansion is declared frozen** in `cra_governance_model.expansion_policy` (JSON). Prefer documentation, CRA/PGC conformance, and reproducibility tooling over admitting new roots or clusters. A CEL governance exception for thaw is **policy intent**—not a runtime admissions gate in current code.

## Philosophical note

Mythar gap-fill is **evidence-constrained invention**: roots and clusters carry FAC-E1 source refs (`Mythar Living Lexicon / Gap-Fill Draft`). They may feed FRA / cognate analysis but remain distinguishable from external comparative corpora (IE mini-set).

## CRA governance model

Exports CRA Justification vs Evidence fields (`docs/architecture/CRA_ReferenceArchitecture_v1.md`). **Aligns with** LRL-INV-05 for evidence-tagging; lineage is **prepared** (`cel_lineage.subject_id` + `binding_status=deferred`), not ledger-bound until CEL IDs are written.

Each root and cluster exports `cra_governance`:

| Field | Graph | Meaning |
|-------|-------|---------|
| **identity** | Justification | `mythar:root:{form}` / `mythar:cluster:{id}` |
| **justification_dependency** | Justification | Why this entry exists (PGC / proposal / core coverage) |
| **evidence_dependency** | Evidence | FAC-E1 source, Proto-World note, test clusters |
| **assurance_level** | Evidence | `experimental` \| `candidate` \| `validated` |
| **lifecycle_state** | Governance | `Draft` → `Review` → `Ratified` → `Active` |
| **cel_lineage** | Evidence | Deferred CEL binding; `subject_id` = `evidence_id` |
| **revision_history** | Governance | Append-only log (includes PGC v1.3 corrections) |

Document policy: `cra_governance_model` in JSON (`mythar.cra_governance.v1`). JSON Schema file: `schemas/mythar_cra_governance.schema.json` *(published; runtime checks use `validate_governance_record` in tests)*.

### Classification defaults

| Class | Assurance | Lifecycle |
|-------|-----------|-----------|
| Core clusters 12–46 | validated | Active |
| Compound / ritual 47–80 | validated | Active |
| Proposals K–L (81–94) | candidate | Review |
| Proposal M (95) | candidate | Review |
| PGC-stable polysemy | validated | Active |
| PGC v1.3 corrections/splits | validated | Active |

### CEL binding (deferred)

As exported, `binding_status=deferred` with `subject_id` = Mythar `evidence_id`. Real `cel_entry_id` values require a FAC-E seed → CEL write **and** a binder that updates lineage (not automatic today). Charter: `docs/governance/CEL_Charter_v01.md`.

## Proposals A–E

| Proposal | Focus |
|----------|--------|
| **A** | Kinship triad gaps (`pa` / `ma` / `ti` / `ne` / `bro`) |
| **B** | Body–sense inventory (`nu` / `mu` / `si` / `li` / `to` / `be` / `pe` / `kor`) |
| **C** | Motion verbs (`bu` / `re` / `le` / `ga`) |
| **D** | Knowing–spirit set (`wi` / `su` / `ni` / `ve`) |
| **F** | Kra-axis compounds (`lmakra` / `yuckara` — cluster 47) |
| **G** | Blessing / birth triad (`tiki` / `yocfua` / `manalara` — cluster 48) |
| **H** | Naming / blessing / sealing axis (clusters 49–60) |
| **I** | Ritual invocation lines (clusters 61–64) |
| **J** | Extended ritual triads (clusters 65–80) |
| **K** | Proto-World universal gaps (clusters 81–87) |
| **L** | Social/body/action/nature/abstract/logic/spatial roots (clusters 88–94) |
| **M** | PGC corrections / axis validation (cluster 95) |

## Polysemy Governance Contract (PGC)

Mythar v1.3 adopts constitutional polysemy rules:

| ID | Rule |
|----|------|
| **PGC-1** | Polysemy requires a shared semantic axis |
| **PGC-2** | Axes must be explicit in the lexicon entry |
| **PGC-3** | Axes must be constitutional (vowel-core / consonant-force) |
| **PGC-4** | Axes must be testable (≥1 cluster exercising both senses) |
| **PGC-5** | No axis → no polysemy (split or remove weaker sense) |

### Validated polysemy (stable)

| Root | Axis | Senses |
|------|------|--------|
| fi | intensity → purity | fire · sacred-verity |
| ru | flow → life-flow | rest-flow · blood |
| pu | motion → living motion | move · animal |
| vi | perception → awareness → life | knowing-see · living |
| ra | scale → magnitude | intensify · great/big/many |
| ma | origin → life → mother | mother · life/origin |
| ka | weight → authority → age | force/gravity · elder |
| la | elevation → illumination | light · sky/above |
| to | agency | hand · give/take |
| ta | deixis | this/that only |
| du | burden | bad/heavy only |
| nu | sense-aperture | nose/breath · ear |
| ti | diminutive | small / sacred diminutive |

### PGC-5 corrections

| Root | Violation | Action |
|------|-----------|--------|
| to | stone ≠ agency | stone → `ska` / `krato` |
| ta | foot/stand ≠ deixis | foot/stand → `pe` / `taga` |
| du | two ≠ burden | two → `duma` |

PGC v1.3 revision history is recorded on affected roots and cluster 95 under `cra_governance.revision_history`.

## Clusters 12–95

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
| **49** | **makra yufala** | abstract | Makra yufala ro ya | Mother-heart in divine blessing-light |
| **50** | **tina rofua** | kinship | Tina rofua ro ya | Child-name rests in blessed flow |
| **51** | **yakora lamina** | abstract | Yakora lamina ro ya | Divine heart-craft illuminates small name |
| **52** | **sufala yotira** | abstract | Sufala yotira ro ya | Good blessing-light proclaims divine child-force |
| **53** | **krafu yumana** | abstract | Krafu yumana ro ya | Blessed vital force names divine existence |
| **54** | **lamara yufina** | abstract | Lamara yufina ro ya | Light-existence proclaims divine blessed true name |
| **55** | **toraka mafira** | nature | Toraka mafira ro ya | Gate-power proclaims mother-truth |
| **56** | **yukra tifala** | kinship | Yukra tifala ro ya | Knowing-heart blesses child-light |
| **57** | **ramina yokra** | abstract | Ramina yokra ro ya | Proclaimed small-name meets divine heart-force |
| **58** | **fukara lamayu** | abstract | Fukara lamayu ro ya | Blessing-heart-craft in light-existence-divine |
| **59** | **tifura yokala** | kinship | Tifura yokala ro ya | Child-blessing proclaimed in divine force-light |
| **60** | **makora yufina ro** | abstract | Makora yufina ro | Mother-heart proclaims divine blessed true name in peace (seal) |
| **61** | **ebro la kajya lapio mufay** | abstract | Ebro la kajya lapio mufay | Emergence · light · divine-power · light-seed · mother-blessing |
| **62** | **plafo micala haftar** | nature | Plafo micala haftar | Open plain · spark-light essence · protective proclamation |
| **63** | **qaytra blapa torja** | nature | Qaytra blapa torja | Proclaimed life · open protection · affirmed threshold |
| **64** | **vi porka yala morkfu** | abstract | Vi porka yala morkfu | Inner knowing → carried power → divine light → rising blessing |

### Clusters 65–80 (extended ritual triads)

| ID | Forms | Domain | Phrase | Interpretation |
|----|-------|--------|--------|----------------|
| 65 | yafora mikra talu | abstract | Yafora mikra talu | Divine gathering · small heart · present flow |
| 66 | plamu yafika torla | nature | Plamu yafika torla | Mother-ground · truth-power · gate-light |
| 67 | kafro yami supla | nature | Kafro yami supla | Power-rest · divine being · good plain |
| 68 | mufra lakyo tinara | kinship | Mufra lakyo tinara | Mother-breath · light-knowing · child-name |
| 69 | yorfa maklu sipra | abstract | Yorfa maklu sipra | Force-blessing · mother-flow · good proclaimed |
| 70 | plika yofra tamu | nature | Plika yofra tamu | Open power · divine proclaim · this-mother |
| 71 | kafya lorpa minu | abstract | Kafya lorpa minu | Grace-power · light-protect · small spirit |
| 72 | yupra makra silu | abstract | Yupra makra silu | Divine proclaim · mother-heart · good flow |
| 73 | torfa yami plaku | nature | Torfa yami plaku | Gate-blessing · divine being · open power-place |
| 74 | morka yaflu sipta | abstract | Morka yaflu sipta | Rising power · divine flow · good-this |
| 75 | lakra yomu tafra | abstract | Lakra yomu tafra | Light-heart · divine-mother · this proclaimed |
| 76 | plina yofka maru | abstract | Plina yofka maru | Open name · divine craft-power · mother rest |
| 77 | kafro yala sipro | abstract | Kafro yala sipro | Power-rest · divine light · good bearing |
| 78 | mufya plaro tikna | kinship | Mufya plaro tikna | Mother-grace · open rest · child-name |
| 79 | yokru lamfa sipla | abstract | Yokru lamfa sipla | Divine heart-force · mother-light bless · good open |
| 80 | makyo yupra torlu | abstract | Makyo yupra torlu | Mother-knowing · divine proclaim · gate flow |

### Clusters 81–87 (proposal K — universal mini-clusters)

| ID | Forms | Domain | Phrase | Interpretation |
|----|-------|--------|--------|----------------|
| 81 | pa ne ti | kinship | Pa ne ti ro ya | Father–kin–child |
| 82 | si nu to | body | Si nu to kra ro | Eye–ear–hand |
| 83 | fi wa hi | nature | Fi wa hi kra la | Fire–water–tree |
| 84 | wi du ro | abstract | Wi du ro ya | Know–bad–rest |
| 85 | su pu ya | motion | Su pu ya kra | Good–move–divine |
| 86 | be ni la | abstract | Be ni la ro ya | Head–name–light |
| 87 | du kra ro | abstract | Du kra ro ya | Heavy–vital–rest |

### Clusters 88–94 (proposal L — gap-fill demonstration)

| ID | Forms | Domain | Phrase | Interpretation |
|----|-------|--------|--------|----------------|
| 88 | chi ma loi | kinship | Chi ma loi ro ya | Child–mother–friend |
| 89 | sa toh tek | motion | Sa toh tek ya | Speak–give–take |
| 90 | sola luna fe | nature | Sola luna fe kra | Sun–moon–wind |
| 91 | tem reka lo | abstract | Tem reka lo ya | Time–change–love |
| 92 | in ex neta | motion | In ex neta ro | Inside–outside–near |
| 93 | ver never ke | abstract | Ver never ke ya | Truth–false–if |
| 94 | rama ko ru | body | Rama ko ru kra | Feeling-heart–bone–blood |
| 95 | pu hu duma | kinship | Pu hu duma kra | Animal–person–two (PGC) |

**Cluster count: 84** (IDs 12–95 inclusive). Lexicon version **1.3**.

### Proposal L — new atomic roots (selected)

| Root | Meaning | Notes |
|------|---------|-------|
| chi | child / youth | independent of ti=small |
| loi | friend / ally | |
| sha | other / stranger | |
| sa | speech / say | |
| rama | feeling-heart | ra+ma |
| ko | bone / structure | |
| peh / dak / toh / tek | create / break / give / take | |
| nuka | death / end | |
| sola / luna / fe | sun / moon / wind | |
| krato / bura | mountain / path | |
| tem / reka / ver / never | time / change / truth / false | |
| lo / alo / dunu | love / up / fear | alo split from lo |
| tima / sura / nema / ke | few / all / none / if | |
| in / ex / duta / neta | inside / outside / down / near | |
| duma | two / dual | PGC split from du |
| taga | stand / grounded foot | PGC split from ta |

PGC-stable polysemy: `fi` fire+verity; `ru` rest-flow+blood; `pu` move+animal; `vi` knowing-see+living; `ra` scale; `ma` origin-life-mother; `ka` force-elder; `la` elevation-light. Register split: `ver` = cognitive truth; `kor` = anatomical heart vs `rama` = feeling-heart.

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

### Clusters 61–64 (ritual invocation lines)

| ID | Axis | Key new roots |
|----|------|----------------|
| 61 | emergence | `e`, `ebro`, `jya`, `pi`, `kajya`, `lapio`, `mufay` |
| 62 | grounding | `fo`, `haf`, `ca`, `plafo`, `micala`, `haftar` |
| 63 | threshold | `qay`, `bla`, `ja`, `qaytra`, `blapa`, `torja` |
| 64 | growth | `por`, `mor`, `porka`, `yala`, `morkfu` (`vi` particle) |

## Sample invocation

```
Ye kra ro ya
Lmakra yuckara
Tiki yocfua manalara
Makra yufala
Makora yufina ro
Ebro la kajya lapio mufay
Plafo micala haftar
Qaytra blapa torja
Vi porka yala morkfu
Yafora mikra talu
Makyo yupra torlu
Pa ne ti
Fi wa hi
Su pu ya
Du kra ro
Chi ma loi
Sola luna fe
Pu hu duma
Wi su ni ve ro ya
```

## Engine API

```python
from sre.mythar import MytharLexicon

lex = MytharLexicon()
lex.cluster_ids()           # 12..95
lex.list_clusters()         # summaries (includes compound clusters)
lex.gap_fill()              # domain coverage + proposals
lex.compare_proto_world()   # Mythar ↔ Proto-World table
lex.seed_registry(registry) # FAC-E seed into EvidenceRegistry (+ Dantomax if configured)

# CRA governance (from build / JSON)
doc = lex.raw
doc["cra_governance_model"]           # freeze policy + field schema
lex.roots()[0]["cra_governance"]      # per-root CRA record
lex.get_cluster(12)["cra_governance"] # per-cluster CRA record
```

## Demo

```powershell
python scripts/generate_mythar_lexicon.py   # regenerate JSON if needed
python scripts/run_local.py --corpus mythar-lex --dantomax
pytest -q tests/test_mythar_lexicon.py
```
