"""Validate SRE CIH conformance profile against repository artifacts."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "docs" / "conformance" / "SRE_ConformanceProfile_v1.json"
CIH_SPEC = ROOT / "docs" / "specs" / "CIH_ConstitutionalSpecification_v1.md"
CIH_REQUIREMENTS = ROOT / "docs" / "specs" / "CIH_ConformanceRequirements_v1.md"
PROFILE_SCHEMA = ROOT / "schemas" / "cih_conformance_profile.schema.json"
CEL_SCHEMA = ROOT / "schemas" / "cel_entry.schema.json"
CONSTITUTIONAL_TESTS = ROOT / "tests" / "test_constitutional.py"

VALID_CEL_ENTRY_TYPES = {
    "attestation",
    "correspondence",
    "hypothesis",
    "validation",
    "certification",
    "evidence",
    "governance",
}


def _load_profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def _resolve(path_str: str) -> Path:
    return ROOT / path_str.replace("/", "\\") if "\\" not in path_str else ROOT / path_str


class CIHConformanceProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = _load_profile()
        cls.test_source = CONSTITUTIONAL_TESTS.read_text(encoding="utf-8")

    def test_profile_and_spec_artifacts_exist(self) -> None:
        self.assertTrue(PROFILE_PATH.is_file())
        self.assertTrue(CIH_SPEC.is_file())
        self.assertTrue(CIH_REQUIREMENTS.is_file())
        self.assertTrue(PROFILE_SCHEMA.is_file())

    def test_profile_required_top_level_fields(self) -> None:
        for key in (
            "profile_id",
            "profile_version",
            "runtime",
            "cih_spec",
            "entities",
            "invariants",
            "conformance_gates",
            "evidence_bindings",
            "extensions",
        ):
            self.assertIn(key, self.profile, f"missing top-level key: {key}")

    def test_runtime_declares_reference_implementation(self) -> None:
        runtime = self.profile["runtime"]
        self.assertEqual(runtime["implementation_id"], "sre")
        self.assertEqual(runtime["role"], "reference_implementation")

    def test_cih_spec_documents_exist(self) -> None:
        spec = self.profile["cih_spec"]
        self.assertTrue(_resolve(spec["document"]).is_file())
        self.assertTrue(_resolve(spec["conformance_requirements"]).is_file())
        kernel = spec.get("kernel_architecture")
        if kernel:
            self.assertTrue(_resolve(kernel).is_file())
        lrl_spec = spec.get("lrl_specification")
        if lrl_spec:
            self.assertTrue(_resolve(lrl_spec).is_file())
        cra = spec.get("cra_architecture")
        if cra:
            self.assertTrue(_resolve(cra).is_file())

    def test_reconstruction_plane_spec_exists(self) -> None:
        lrl = self.profile.get("reconstruction_plane")
        if not lrl:
            return
        spec_path = lrl.get("specification")
        if spec_path:
            self.assertTrue(_resolve(spec_path).is_file())

    def test_all_entity_modules_exist(self) -> None:
        for entity in self.profile["entities"]:
            module = entity["implementation"]["module"]
            path = _resolve(module)
            self.assertTrue(path.is_file(), f"{entity['entity_id']}: missing {module}")
            if schema := entity["implementation"].get("schema"):
                self.assertTrue(_resolve(schema).is_file(), f"missing schema {schema}")

    def test_core_cih_entities_present(self) -> None:
        core_ids = {e["entity_id"] for e in self.profile["entities"] if e["classification"] == "core"}
        required = {
            "ProjectSpec",
            "EvidenceBaseline",
            "ArchitectureReview",
            "CIHApproval",
            "SovereignCertificate",
            "GovernanceTrace",
        }
        self.assertTrue(required.issubset(core_ids), f"missing core entities: {required - core_ids}")

    def test_core_cih_gates_mapped_to_tests(self) -> None:
        core_gates = [
            g for g in self.profile["conformance_gates"] if g["classification"] == "core"
        ]
        self.assertEqual(len(core_gates), 5)
        for gate in core_gates:
            self.assertTrue(gate["gate_id"].startswith("CIH-"))
            self.assertIn(f"def {gate['test_name']}", self.test_source)

    def test_cih_invariants_have_enforcement(self) -> None:
        for inv in self.profile["invariants"]:
            self.assertIn("invariant_id", inv)
            self.assertIn(inv["enforcement"], {"enforced", "observed", "documented"})

    def test_evidence_bindings_use_valid_cel_entry_types(self) -> None:
        cel_types = json.loads(CEL_SCHEMA.read_text(encoding="utf-8"))
        allowed = set(cel_types["properties"]["entry_type"]["enum"])
        for binding in self.profile["evidence_bindings"]:
            for entry_type in binding.get("cel_entry_types") or []:
                self.assertIn(entry_type, allowed)
                self.assertIn(entry_type, VALID_CEL_ENTRY_TYPES)

    def test_extension_modules_exist(self) -> None:
        for ext in self.profile["extensions"]:
            path = _resolve(ext["module"])
            self.assertTrue(path.is_file(), f"{ext['extension_id']}: missing {ext['module']}")

    def test_api_binding_handlers_exist(self) -> None:
        for binding in self.profile.get("api_bindings") or []:
            self.assertTrue(_resolve(binding["handler"]).is_file())

    def test_reconstruction_plane_modules_exist(self) -> None:
        lrl = self.profile.get("reconstruction_plane")
        if not lrl:
            return
        for component in lrl.get("components") or []:
            self.assertTrue(
                _resolve(component["module"]).is_file(),
                f"missing LRL component {component['component_id']}",
            )
        for language in lrl.get("reference_languages") or []:
            if corpus := language.get("corpus"):
                self.assertTrue(_resolve(corpus).is_file(), f"missing corpus {corpus}")

    def test_reconstruction_plane_cel_bindings_valid(self) -> None:
        lrl = self.profile.get("reconstruction_plane")
        if not lrl:
            return
        for binding in lrl.get("cel_bindings") or []:
            self.assertIn(binding["cel_entry_type"], VALID_CEL_ENTRY_TYPES)

    def test_sre_version_matches_package(self) -> None:
        spec = importlib.util.find_spec("sre")
        assert spec and spec.origin
        init_path = Path(spec.origin)
        content = init_path.read_text(encoding="utf-8")
        self.assertIn(self.profile["runtime"]["version"], content)


if __name__ == "__main__":
    unittest.main()
