# Licensing and attribution

Copyright © 2026 Druhin Tarafder, except where separately attributed.

The following license grants apply **only to original material whose copyright is held by the author**:

| Material | Paths | License |
| --- | --- | --- |
| Original programs, verification scripts and regression tests | `evidence/reproduce.py`, `evidence/scripts/**`, `evidence/tools/**`, `evidence/tests/**` | [MIT](LICENSE-MIT.txt) |
| GitHub Actions verification workflow | `.github/workflows/verify-evidence.yml` | [MIT](LICENSE-MIT.txt) |
| Mathematical proof objects, certificate registries and benchmark data | `evidence/proofs/**`, `evidence/artifacts/**`, `evidence/benchmarks/**` | [CC BY 4.0](LICENSE-CC-BY-4.0.md) |
| Documentation and citation data | `README.md`, `REPRODUCING.md`, `PROVENANCE.md`, `THIRD_PARTY_NOTICES.md`, `CITATION.cff`, `SHA256SUMS`, `LICENSE.md` and `LICENSE-CC-BY-4.0.md` | [CC BY 4.0](LICENSE-CC-BY-4.0.md) |
| MIT license text | `LICENSE-MIT.txt` | MIT license notice for the above original software and configuration; reproduced unchanged |
| Git and repository configuration | `.gitattributes`, `.gitignore` | [MIT](LICENSE-MIT.txt) |

**Third-party dependencies.** The build scripts fetch DRAT-trim (MIT) and CakeML `cake_lpr` (upstream three-clause BSD-style terms) from their official repositories at fixed revisions. Their source trees are not included here, and neither license above modifies their terms. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for project credits, revision identifiers, and licensing references. Citations in bibliographic or research material do not imply copyright ownership.

**Attribution.** When reusing CC BY 4.0 material, credit Druhin Tarafder, identify the title and repository revision, link to [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), and indicate modifications. Software redistributed under MIT must retain the required copyright and permission notice. See the complete licenses for governing terms.

The accompanying manuscript/LaTeX is not distributed in this repository version. When published separately, its licensing must be stated with that publication. No rights are asserted over third-party works.
