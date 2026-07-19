# FRA Methodology

Nine-stage Fact-anchored Reconstruction Algorithm (FRA) for SRE v0.1.

## Pseudocode

```
FUNCTION reconstruct_language(target_language, time_period, evidence_sources):
    # 1. OBSERVE
    observed = collect_evidence(evidence_sources)
    metrics = analyze_distribution(observed)

    # 2. EXTRACT
    patterns = []
    FOR evidence IN observed:
        features = extract_all_features(evidence)
        patterns.append(features)

    # 3. BUILD
    proto = initialize_proto_model(target_language, time_period)
    proto.ingest(patterns)

    # 4. TEST
    tests = run_tests(proto, observed)
    drift = measure_drift(proto, observed)

    # 5. REFINE
    WHILE drift > threshold OR tests < quality_gate:
        proto = refine(proto, patterns, drift)
        tests = run_tests(proto, observed)
        drift = measure_drift(proto, observed)

    # 6. ALIGN
    aligned = align_with_reference(proto, target_language, time_period)

    # 7. VALIDATE
    validation = evidence_registry.validate_reconstruction(aligned.id)
    IF NOT validation.is_valid:
        RETURN failure(validation)

    # 8. CERTIFY
    certificate = issue_certificate(aligned, validation)

    # 9. ARCHIVE
    archive = archive_reconstruction(aligned, certificate, evidence_sources)
    RETURN {aligned, certificate, archive}
```

## Constraints

- Evidence-constrained iteration
- Drift detection and progressive refinement
- Constitutional validation before certification

## Wire targets

- `ChronologicalReconstruction.reconstruct_language` → `POST /api/v1/reconstruction`
- Stage scaffolding: `src/sre/fra/stages.py`
