# SRE v1.0.0 Benchmark Corpus Documentation

## Overview

This document describes the benchmark corpora included in SRE v1.0.0 for validation, testing, and demonstration purposes. These corpora are designed to test various aspects of the reconstruction engine including constitutional governance, Bayesian phylogenetic inference, automatic correspondence induction, and evidence validation.

## Corpus Summary

| Corpus ID | File | Languages | Evidence Items | Purpose | License |
|-----------|------|-----------|-----------------|---------|---------|
| `fra_test_v01` | `fra_corpus_v01.json` | 2 (Mythar, Related Branch) | 16 | FRA cycle testing | Apache-2.0 |
| `ie_cognate_mini_v01` | `ie_cognate_mini_v01.json` | 5 (LAT, SPA, FRA, SKT, PIE) | 80 | Indo-European validation | Apache-2.0 |
| `ie_cognate_expanded_v01` | `ie_cognate_expanded_v01.json` | 15+ | 500+ | Extended IE analysis | Apache-2.0 |
| `mythar_lexicon_v01` | `.json` | 1 (Mythar) | 2000+ | Lexicon clustering | Mythar License |

## 1. FRA Test Corpus (`fra_test_v01`)

### 1.1 Description

Synthetic corpus designed for testing the nine-stage FRA (Foundational Reconstruction Architecture) cycle. This corpus demonstrates the constitutional evidence flow through FAC-E validation, FRA processing, and FAC-V certification.

### 1.2 Languages

- **MYT (Mythar)**: Synthetic language with 4 chronological phases
- **REL (Related Branch)**: Hypothetical related language with 4 chronological phases

### 1.3 Evidence Structure

Each language contains 4 phases with the following evidence types:
- **Inscriptions**: Textual evidence with site and date metadata
- **Lexical Items**: Individual word forms with meanings
- **Phonological Rules**: Sound change patterns
- **Corpus Samples**: Extended text passages

### 1.4 Key Features

- **Chronological Stratification**: Evidence organized by temporal phases
- **Sound Change Demonstration**: Embedded phonological rules (e.g., `a → ah / _r`)
- **Semantic Consistency**: Glosses maintain semantic coherence across phases
- **Metadata Completeness**: All evidence includes source and temporal metadata

### 1.5 Usage

```bash
python scripts/run_local.py --corpus mythar
```

### 1.6 Validation Purpose

- FAC-E validation gate testing
- FRA cycle orchestration verification
- Constitutional evidence flow validation
- CIH attestation testing

## 2. Indo-European Mini Corpus (`ie_cognate_mini_v01`)

### 2.1 Description

Miniature Indo-European comparative dataset containing standard cognate sets from classical sources. Designed for validation of phylogenetic inference and correspondence induction methods.

### 2.2 Languages

| Code | Language | Period | Evidence Items |
|------|----------|--------|----------------|
| LAT | Latin | Classical | 16 |
| SPA | Spanish | Modern | 16 |
| FRA | French | Modern | 16 |
| SKT | Sanskrit | Vedic | 16 |
| PIE | Proto-Indo-European | Reconstructed | 6 |

### 2.3 Semantic Categories

The corpus covers 5 semantic domains with 16 lexical items per language:

**Kinship Terms** (2 items):
- father: pater/padre/père/pitar/*ph₂tēr
- mother: mater/madre/mère/matar/*méh₂tēr

**Body Parts** (6 items):
- foot: pes/pie/pied/pad/péd-
- heart: cor/corazón/coeur/hrd/hṛd-
- eye: oculus/ojo/œil/akṣi/h₃ekʷ-
- tooth: dens/diente/dent/dant/*h₃dont-
- knee: genu/rodilla/genou/jānu/*ǵónu
- blood: sanguis/sangre/sang/asṛj-*h₁éh₁m-

**Numerals** (5 items):
- one: unus/uno/un/eka/*óynos
- two: duo/dos/deux/dva/*dwóh₁
- three: tres/tres/trois/tri/*tréyes
- four: quattuor/cuatro/quatre/catur*kʷetwóres
- five: quinque/cinco/cinq/pañca*pénkʷe

**Core Verbs** (4 items):
- be: est/ser/être/as-*h₁es-
- bear: ferre/llevar/porter/bhar-*bʰer-
- know: gnoscere/conocer/connaitre/jñā-*ǵneh₃-
- eat: edere/comer/manger/ad-*h₁ed-

### 2.4 Sources

All forms are sourced from standard Indo-European textbooks:
- Fortson, Benjamin W. IV. 2010. *Indo-European Language and Culture*. 2nd ed. Wiley-Blackwell.
- Beekes, Robert S. P. 2011. *Comparative Indo-European Linguistics*. 2nd ed. John Benjamins.

### 2.5 Metadata Standards

Each evidence item includes:
- `evidence_id`: Unique identifier following pattern `evid_{code}_{semantic}`
- `type`: Always "lexical_item" for daughter languages, "phonological_rule" for PIE
- `form`: Phonetic transcription
- `meaning`: English gloss
- `metadata.source`: Bibliographic reference
- `metadata.date`: Temporal information where applicable

### 2.6 Usage

```bash
python scripts/run_local.py --corpus ie --dantomax --with-cih
```

### 2.7 Validation Purpose

- Bayesian phylogenetic inference validation
- Automatic correspondence induction testing
- Sound change pattern discovery
- Cross-linguistic consistency verification
- Historical reconstruction accuracy assessment

### 2.8 Expected Results

Based on established Indo-European scholarship:
- **Grouping**: Romance languages (SPA, FRA) should cluster separately from SKT
- **Root Recovery**: PIE reconstructions should match standard forms
- **Sound Changes**: Regular sound changes should be discoverable (e.g., p→f in Romance)
- **Branch Support**: High bootstrap support for established subgroupings

## 3. Indo-European Expanded Corpus (`ie_cognate_expanded_v01`)

### 3.1 Description

Extended Indo-European dataset with broader language coverage and increased lexical diversity. Designed for stress testing and scalability validation.

### 3.2 Language Coverage

Includes 15+ Indo-European languages from major branches:
- **Germanic**: English, German, Dutch, Gothic
- **Romance**: Spanish, French, Italian, Portuguese, Romanian
- **Slavic**: Russian, Polish, Czech
- **Indo-Iranian**: Sanskrit, Hindi, Persian
- **Celtic**: Irish, Welsh
- **Baltic**: Lithuanian, Latvian
- **Greek**: Ancient Greek, Modern Greek

### 3.3 Lexical Coverage

500+ cognate sets covering:
- Extended kinship terminology
- Comprehensive body part vocabulary
- Full numeral systems (1-10, teens, hundreds)
- Agricultural and pastoral vocabulary
- Natural world terminology
- Basic verb lexicon

### 3.4 Usage

```bash
python scripts/run_local.py --corpus ie-expanded
```

### 3.5 Validation Purpose

- Scalability testing for large datasets
- Complex phylogenetic tree inference
- Robustness to data heterogeneity
- Computational performance benchmarking
- Cross-branch correspondence discovery

## 4. Mythar Lexicon Corpus (`mythar_lexicon_v01`)

### 4.1 Description

Comprehensive Mythar language lexicon for advanced linguistic analysis and lexicon clustering validation. This corpus contains Mythar IP and is subject to separate licensing.

### 4.2 Content

- 2000+ lexical items with detailed semantic classification
- Phonological feature annotations
- Etymological reconstructions where available
- Usage examples from corpus data
- Semantic field classifications

### 4.3 License

**Mythar License** - Separate from Apache-2.0 framework license. See `LICENSES/Mythar_License.md` for details.

### 4.4 Usage

```bash
python scripts/run_local.py --corpus mythar-lex
```

### 4.5 Validation Purpose

- Lexicon clustering algorithm validation
- Semantic field analysis testing
- Advanced correspondence induction
- Mythar-specific linguistic analysis

## 5. Corpus Schema

### 5.1 JSON Structure

All corpora follow the standard SRE corpus schema:

```json
{
  "corpus_id": "string",
  "description": "string",
  "references": ["string"],
  "languages": [
    {
      "code": "string",
      "name": "string",
      "periods": [
        {
          "name": "string",
          "evidence": [
            {
              "evidence_id": "string",
              "type": "lexical_item|inscription|phonological_rule|corpus_sample",
              "form": "string",
              "meaning": "string",
              "text": "string",
              "gloss": "string",
              "rule": "string",
              "metadata": {
                "source": "string",
                "date": "string",
                "site": "string"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 5.2 Schema Validation

Corpora are validated against JSON schema in `schemas/corpus_schema.json`. Validation checks:
- Required field presence
- Data type correctness
- Enum value constraints
- Reference format compliance
- Metadata completeness

## 6. Corpus Quality Standards

### 6.1 Evidence Validation

All evidence must pass FAC-E validation:
- **FAC-E1**: Source validation - bibliographic references or provenance data
- **FAC-E2**: Structural validation - JSON schema compliance
- **FAC-E3**: Semantic validation - linguistic consistency and coherence
- **FAC-E4**: Constitutional accept - alignment with constitutional constraints

### 6.2 Metadata Standards

- **Source References**: All evidence must include source references
- **Temporal Data**: Dating information where applicable
- **Phonetic Accuracy**: IPA or standard phonetic transcription
- **Semantic Clarity**: Unambiguous glosses and meanings
- **Cross-References**: Related evidence items linked where appropriate

### 6.3 Linguistic Standards

- **Phonological Consistency**: Sound changes must be phonologically plausible
- **Semantic Stability**: Meanings must be consistent across cognate sets
- **Historical Plausibility**: Reconstructions must align with established scholarship
- **Typological Reasonableness**: Forms must be typologically plausible

## 7. Corpus Usage Guidelines

### 7.1 Testing

For development and testing:
```bash
# Quick test with synthetic corpus
python scripts/run_local.py --corpus mythar

# Validation with real data
python scripts/run_local.py --corpus ie
```

### 7.2 Research

For research applications:
```bash
# Extended analysis
python scripts/run_local.py --corpus ie-expanded --dantomax --with-cih

# Lexicon analysis
python scripts/run_local.py --corpus mythar-lex --show-cel
```

### 7.3 API Access

Corpora can be accessed via the HTTP API:
```bash
# Start API server
sre-api

# Access corpus
curl http://127.0.0.1:8010/api/corpus/ie_cognate_mini_v01
```

## 8. Corpus Maintenance

### 8.1 Version Control

- Corpus versions follow semantic versioning (v01, v02, etc.)
- Changes are documented in CHANGELOG.md
- Backward compatibility maintained where possible

### 8.2 Contribution Guidelines

New corpora should:
1. Follow the standard JSON schema
2. Include comprehensive metadata
3. Pass all FAC-E validation gates
4. Include source references
5. Document linguistic assumptions
6. Provide validation results

### 8.3 Quality Assurance

All corpora undergo:
- Schema validation
- FAC-E validation testing
- Linguistic consistency checking
- Cross-reference verification
- Metadata completeness audit

## 9. Corpus Limitations

### 9.1 Synthetic Corpora

- May not reflect natural language complexity
- Sound changes may be simplified
- Semantic relationships may be idealized

### 9.2 Real Corpora

- Subject to scholarly disagreement
- May contain errors or uncertainties
- Limited by available source data
- Temporal coverage may be incomplete

### 9.3 General Limitations

- Corpus size affects statistical power
- Language bias toward well-studied families
- Diachronic coverage may be uneven
- Areal diffusion effects may complicate analysis

## 10. Future Corpus Development

### 10.1 Planned Additions

- **Austronesian**: Pacific island language families
- **Uralic**: Finno-Ugric and Samoyedic languages
- **Bantu**: Niger-Congo language family
- **Sino-Tibetan**: East Asian language families
- **Australian**: Indigenous Australian languages

### 10.2 Enhancement Goals

- Increased temporal coverage
- Expanded semantic domains
- Enhanced metadata standards
- Improved cross-referencing
- Integration with external databases

## 11. Contact and Support

For corpus-related questions:
- **Documentation**: See `docs/corpora/README.md`
- **Issues**: GitHub issue tracker
- **Contributions**: See `CONTRIBUTING.md`

---

**Document Version**: 1.0  
**SRE Version**: 1.0.0  
**Date**: July 21, 2026  
**Status**: Release
