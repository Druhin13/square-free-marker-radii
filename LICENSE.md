# Licenses and attribution

Copyright © 2026 Druhin Tarafder, except where another original rights holder is identified.

This repository contains **different kinds of material under different licenses**. The licenses are **not interchangeable**. The following directory/path rules apply to original materials owned by Druhin Tarafder:

| Material | Paths | License |
| --- | --- | --- |
| Verification and generation software, scripts, code and tests | `evidence/scripts/**`, `evidence/tools/**`, `evidence/tests/**`, `evidence/reproduce.py` | [MIT](LICENSE-MIT.txt) |
| Preserved historical workflow contracts and independent repository verification CI | `evidence/.github/workflows/**`, `.github/workflows/verify-evidence.yml` | [MIT](LICENSE-MIT.txt) for original code/workflow content |
| Original mathematical proof certificates, SAT models, witness tables and research data | `evidence/proofs/**`, `evidence/artifacts/**`, `evidence/benchmarks/**` | [CC BY 4.0](LICENSE-CC-BY-4.0.md) |
| Historical manuscript and bibliography LaTeX sources | `evidence/paper/main.tex`, `evidence/paper/references.bib` | [CC BY 4.0](LICENSE-CC-BY-4.0.md) |
| Original documentation and citation metadata | `README.md`, `REPRODUCING.md`, `PROVENANCE.md`, `CITATION.cff`, `evidence/REPRODUCING_PORTABLE.md`, `SHA256SUMS`, this licensing index | [CC BY 4.0](LICENSE-CC-BY-4.0.md) |
| Repository housekeeping and plain-text integrity configuration | `.gitignore`, `.gitattributes` | [MIT](LICENSE-MIT.txt) |

**Third-party material:** the independently maintained [DRAT-trim](https://github.com/marijnheule/drat-trim) and [CakeML cake_lpr](https://github.com/tanyongkiam/cake_lpr) sources are not included. Build scripts fetch specific revisions; those sources and their copyright notices retain their original MIT and BSD-3-Clause terms respectively. Neither the above MIT nor CC BY 4.0 grants claim ownership of or relicense third-party software. Bibliographic citations likewise do not confer any rights in cited works.

**Historical bytes:** the 52 original proof artifacts and their four manifests remain byte-for-byte identical to the verified private archive. The historical `evidence/paper/` files contain an older draft and are **not** the current submission manuscript. Their inclusion and CC BY 4.0 licensing do not imply they are the recommended paper to cite.

**Attribution for CC BY material:** credit *Druhin Tarafder*, identify the title and repository URL, include a link to CC BY 4.0, and indicate if modifications were made. See the full [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) for the governing terms. The MIT notice must be retained when redistributing substantial portions of the MIT-covered code.

The licenses apply to the original material under this author's authority only. This notice does not change any independently held third-party rights or give a warranty about research correctness.
