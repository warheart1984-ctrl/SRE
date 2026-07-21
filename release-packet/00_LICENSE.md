# SRE v1.0.0 License Documentation

## License Overview

Sovereign Reconstruction Engine (SRE) v1.0.0 is released under a dual-license structure to properly distinguish between the open-source framework and proprietary creative assets.

## Framework License: Apache-2.0

### License Text

The SRE framework (code, specifications, and open documentation) is licensed under the Apache License, Version 2.0.

```
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
   [... Full license text in LICENSE file ...]

   Copyright 2026 HYFAL / Sovereign Reconstruction Engine contributors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
```

### What is Covered

The Apache-2.0 license covers:

- **Source Code**: All Python source code in `src/` and `packages/fae/`
- **Framework Specifications**: Technical documentation in `docs/` (excluding IP sections)
- **Test Code**: All test files in `tests/`
- **Configuration**: Build configuration, CI/CD workflows
- **Open Documentation**: User guides, API documentation, technical reports
- **Benchmark Corpora**: Indo-European corpora (Apache-2.0 compatible)
- **Synthetic Corpora**: Mythar test corpus (Apache-2.0 compatible)

### Apache-2.0 Summary

**Permissions**:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Patent use
- ✅ Private use

**Conditions**:
- ⚠️ License and copyright notice
- ⚠️ State changes
- ⚠️ Document significant changes

**Limitations**:
- ❌ Liability
- ❌ Warranty
- ❌ Trademark use

### Framework Copyright Holder

**Copyright**: © 2026 HYFAL / SRE  
**License**: Apache License 2.0  
**SPDX Identifier**: Apache-2.0

## Mythar Creative Assets License

### License Type

Mythar creative assets are licensed under a separate proprietary license.

### License Document

Full license text: `LICENSES/Mythar_License.md`

### What is Covered

The Mythar license covers:

- **Mythar Language**: Lexicon, grammar, writing system, cosmology
- **Sound Laws**: Mythar-specific phonological rules
- **Ritual Syntax**: Mythar ceremonial language patterns
- **Reconstruction Lineage**: Mythar historical reconstruction
- **Creative Works**: Mythar stories, mythology, cultural elements
- **Mythar Lexicon Corpus**: `data/mythar_lexicon_v01.json`

### License Summary

**License Types Available**:
- **Personal License**: Non-commercial use only
- **Creator License**: Commercial use in small projects
- **Studio License**: Commercial use in large productions
- **Enterprise License**: AI model integration and platform use

**Restrictions**:
- ❌ Claim authorship of Mythar
- ❌ Sell Mythar independently
- ❌ Remove CEL lineage or CIH certification
- ❌ Alter reconstruction history or evidence
- ❌ Use Mythar outside license scope

**Required Attribution**:
```
Mythar language © 2026 Jon Halstead. Used under license.
```

### Mythar Copyright Holder

**Copyright**: © 2026 Jon Halstead  
**License**: Mythar License v1.0  
**License File**: `LICENSES/Mythar_License.md`

## Third-Party Licenses

### Dependencies

All third-party dependencies use permissive licenses compatible with Apache-2.0:

| Package | Version | License | Compatibility |
|---------|---------|---------|---------------|
| fastapi | 0.139.2 | MIT | ✅ Compatible |
| uvicorn | 0.51.0 | BSD | ✅ Compatible |
| pydantic | 2.13.4 | MIT | ✅ Compatible |
| httpx | 0.28.1 | Apache-2.0 | ✅ Compatible |
| numpy | 2.5.1 | BSD | ✅ Compatible |
| pytest | 9.1.1 | MIT | ✅ Compatible |
| ruff | 0.15.22 | MIT | ✅ Compatible |
| python-dotenv | 1.2.2 | BSD | ✅ Compatible |
| pyyaml | 6.0.3 | MIT | ✅ Compatible |

### License Compatibility

All third-party licenses are compatible with Apache-2.0:
- **MIT**: Permissive, no copyleft
- **BSD**: Permissive, minimal requirements
- **Apache-2.0**: Same license, fully compatible

## Usage Guidelines

### Using the Framework Only

If you only use the SRE framework (Apache-2.0 code) without Mythar creative assets:

```bash
# Install framework
pip install sovereign-reconstruction-engine

# Use with your own corpora
python -c "from sre.linguistics import bayesian_phylogeny; ..."
```

**License Requirements**: Apache-2.0 (include license notice, state changes)

### Using with Mythar Creative Assets

If you use Mythar creative assets:

```bash
# Install framework
pip install sovereign-reconstruction-engine

# Obtain Mythar license
# Contact: warheart1984@gmail.com
# See: LICENSES/Mythar_License.md

# Use Mythar corpus
python scripts/run_local.py --corpus mythar-lex
```

**License Requirements**: 
- Apache-2.0 for framework
- Mythar License for creative assets
- Required attribution for Mythar

### Distribution

#### Framework Only Distribution

```bash
# Distribute framework code
git clone https://github.com/warheart1984-ctrl/mythar-sre.git
# Include LICENSE file
# Include Apache-2.0 notice
```

**Requirements**: Apache-2.0 compliance

#### Framework + Mythar Distribution

```bash
# Distribute framework code
git clone https://github.com/warheart1984-ctrl/mythar-sre.git
# Include LICENSE file (Apache-2.0)
# Include LICENSES/Mythar_License.md
# Include required attribution
```

**Requirements**: 
- Apache-2.0 compliance for framework
- Mythar License compliance for creative assets
- Proper attribution for both

## Commercial Use

### Framework Commercial Use

**Allowed**: ✅ Yes, under Apache-2.0

**Requirements**:
- Include Apache-2.0 license
- Include copyright notice
- State significant changes
- No warranty/liability from original authors

### Mythar Commercial Use

**Allowed**: ⚠️ Requires appropriate Mythar license

**License Types**:
- **Creator License**: Small commercial projects
- **Studio License**: Large commercial productions
- **Enterprise License**: AI/platform integration

**Contact**: warheart1984@gmail.com for licensing

## Attribution Requirements

### Framework Attribution

For Apache-2.0 framework:

```
Sovereign Reconstruction Engine (SRE)
Copyright 2026 HYFAL / SRE
Licensed under the Apache License, Version 2.0
```

### Mythar Attribution

For Mythar creative assets:

```
Mythar language © 2026 Jon Halstead. Used under license.
```

### Combined Attribution

When using both:

```
Sovereign Reconstruction Engine (SRE)
Copyright 2026 HYFAL / SRE
Licensed under the Apache License, Version 2.0

Mythar language © 2026 Jon Halstead. Used under [license type] license.
```

## License Violations

### What Constitutes Violation

**Apache-2.0 Violations**:
- Removing license notices
- Claiming authorship of framework code
- Failing to state significant changes
- Using trademark without permission

**Mythar License Violations**:
- Using Mythar without appropriate license
- Claiming authorship of Mythar
- Selling Mythar independently
- Removing CEL lineage or CIH certification
- Altering Mythar reconstruction history

### Reporting Violations

**Framework Violations**:
- Contact: warheart1984@gmail.com
- Repository: https://github.com/warheart1984-ctrl/mythar-sre/issues

**Mythar Violations**:
- Contact: warheart1984@gmail.com
- Legal action may be pursued

## License FAQ

### Can I use SRE in a commercial project?

**Framework**: Yes, under Apache-2.0  
**Mythar assets**: Requires appropriate Mythar license

### Can I modify SRE and distribute it?

**Framework**: Yes, under Apache-2.0 (must state changes)  
**Mythar assets**: No, cannot modify Mythar creative assets

### Can I use SRE in an AI/ML project?

**Framework**: Yes, under Apache-2.0  
**Mythar assets**: Requires Enterprise License

### Do I need to attribute SRE?

**Framework**: Yes, include Apache-2.0 notice  
**Mythar assets**: Yes, include required attribution

### Can I use SRE without Mythar?

**Yes**: The framework is fully functional without Mythar creative assets. Use Indo-European corpora or your own data.

## License Contacts

### Framework Licensing

**Questions**: warheart1984@gmail.com  
**Repository**: https://github.com/warheart1984-ctrl/mythar-sre  
**License File**: LICENSE

### Mythar Licensing

**Questions**: warheart1984@gmail.com  
**License File**: LICENSES/Mythar_License.md  
**Licensing Model**: docs/commercial/Mythar_LicensingModel_v1.md

## Legal Disclaimer

This document is provided for informational purposes only and does not constitute legal advice. For specific legal questions regarding licensing, please consult with legal counsel.

## License Summary Table

| Component | License | Commercial Use | Modification | Distribution | Attribution |
|-----------|---------|----------------|--------------|--------------|--------------|
| Framework Code | Apache-2.0 | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Required |
| Framework Docs | Apache-2.0 | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Required |
| IE Corpora | Apache-2.0 | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Required |
| Mythar Assets | Mythar License | ⚠️ Licensed | ❌ No | ⚠️ Licensed | ⚠️ Required |
| Mythar Corpus | Mythar License | ⚠️ Licensed | ❌ No | ⚠️ Licensed | ⚠️ Required |

## Additional Resources

- **Apache-2.0 Full Text**: LICENSE
- **Mythar License**: LICENSES/Mythar_License.md
- **Mythar IP Documentation**: docs/ip/README.md
- **Mythar Licensing Model**: docs/commercial/Mythar_LicensingModel_v1.md
- **Apache License FAQ**: https://www.apache.org/licenses/LICENSE-2.0FAQ.html

---

**Document Version**: 1.0  
**SRE Version**: 1.0.0  
**Date**: July 21, 2026  
**Status**: Release  
**Legal Status**: For informational purposes only
