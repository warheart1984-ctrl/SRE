# HLRMAIAgent

High-Level Reconstruction Model AI Agent for SRE v0.1.

## Responsibilities

- Pattern extraction (inscriptions, lexicon, phonology)
- Proto-form hypothesis generation and ranking
- FRA-guided refinement
- Constitutional validation via EvidenceRegistry

## Methods

| Method | Wire target |
|--------|-------------|
| `analyze_evidence_patterns(evidence_list)` | `POST /api/v1/ai/analyze` |
| `predict_proto_forms(analysis)` | `POST /api/v1/ai/protoforms` |
| `refine_reconstruction(proto_form, analysis, iteration)` | Internal FRA REFINE |

## Analysis modules

- `LexicalAnalyzer`
- `PhonologicalAnalyzer`
- `CognateDetector`

## AI constraints (Article IV)

- No unconstrained generation
- All outputs evidence-anchored
- All outputs governance-traceable
