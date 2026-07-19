# Enterprise Topology

Layered microservice + governance topology for SRE v0.1.

## ASCII deployment diagram

```
                         ┌──────────────────────────────────────────┐
                         │        CLIENT / INTERACTION LAYER        │
                         │------------------------------------------│
                         │  • Reconstruction Console (UI)           │
                         │  • Evidence Viewer                       │
                         │  • CIH Governance Dashboard              │
                         └──────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE EXECUTION LAYER                              │
│------------------------------------------------------------------------------│
│  Evidence Services:                                                           │
│    • EvidenceRegistry (FAC-E1–E4)                                             │
│    • DantomaxClient (Integrity Oracle)                                        │
│                                                                              │
│  Reconstruction Services:                                                     │
│    • ChronologicalReconstruction (FRA Engine)                                 │
│    • MCRLRosettaEngine (Temporal Mapping)                                     │
│                                                                              │
│  AI Services:                                                                 │
│    • HLRMAIAgent (Pattern Extraction, Proto-Forms, Refinement)                │
│                                                                              │
│  Governance Services:                                                         │
│    • FAECLanguageReconstructionService (CIH)                                  │
│    • Sovereign Certificate Authority                                           │
└──────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────┐
│                         GOVERNANCE & OVERSIGHT LAYER                          │
│------------------------------------------------------------------------------│
│  • HYFAL Executive Council                                                    │
│  • Governance Consensus Map                                                   │
│  • Sovereign Ledger Explorer                                                  │
│  • Constitutional Trace Engine                                                │
└──────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────┐
│                         PLATFORM & INFRASTRUCTURE LAYER                       │
│------------------------------------------------------------------------------│
│  • Kubernetes (Orchestration)                                                 │
│  • Service Mesh (mTLS, Policy, Observability)                                 │
│  • OpenTelemetry (Tracing)                                                    │
│  • Prometheus / Grafana (Monitoring)                                          │
│  • Secrets Management (Vault / KMS)                                           │
│  • Container Registry                                                         │
└──────────────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────────────────┐
│                         EVIDENCE & DATA LAYER                                 │
│------------------------------------------------------------------------------│
│  • Immutable Evidence Store (Hash-Chained)                                    │
│  • Reconstruction Artifact Store                                               │
│  • Temporal Mapping Store (MCRL)                                              │
│  • Dantomax Ledger                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

Aligned with CIEMS: Constitution → Specification → Conformance → Implementation → Deployment → Stewardship.

## Microservices

EvidenceRegistry · ChronologicalReconstruction · HLRMAIAgent · CIH Service · MCRLRosettaEngine
