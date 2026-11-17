# Evidence provenance, trust boundaries and upstream software

## Proven original proof objects

The evidence contains exactly **52 original, byte-for-byte preserved proof objects (115,720,432 bytes)**. Four immutable registries in `evidence/artifacts/` describe and hash those objects:

| Manifest | Registered objects |
| --- | ---: |
| `manifest.json` | 21 |
| `subgroup-manifest.json` | 23 |
| `subgroup-positive-manifest.json` | 3 |
| `exact-symmetry-addendum-manifest.json` | 5 |

All four registries and the original proof files remain unchanged from the tested computational baseline. `SHA256SUMS` additionally lists **all** other files in the public repository. The expected proof corpus is not reconstructed from historical solver logs: these are the archival source proof objects, which can be checked independently.

## What the verifier establishes

Independent programs check finite packing/covering clauses, source witnesses, marker tables, the 30-subgroup classification, and selected DRAT/LRAT refutations. `evidence/reproduce.py` checks original certificate identities before and after each of seven families.

**Not mechanically proved by the certificate checker:** the classical Hall–Thue recurrence and infinite square-freeness facts, the handwritten two-sided extension/separator lemmas, or any universal originality/priority claim. These retain their own mathematical trust boundaries in the paper.

Fresh controlled CaDiCaL searches described in the manuscript (four negative and three radius-five positive instances) are later reproducibility experiments. Their timings must not be described as the original historical discovery timings. The release prioritizes independently checkable theorem certificates and additionally includes optional source to rerun all seven **new** controlled experiments. `evidence/benchmarks/fresh-search-results.json` records their source hashes, solver identity, output digests and measured resources without retaining large ephemeral solver outputs. Historical original discovery runtimes remain unknown.

## Third-party tools

- **DRAT-trim**, maintained by Marijn Heule and contributors: https://github.com/marijnheule/drat-trim ; commit `effa1dcce85c878236f8313133dff1a2b766cd7c`; upstream MIT license.
- **CakeML `cake_lpr`**, maintained by its upstream authors: https://github.com/tanyongkiam/cake_lpr ; commit `033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2`; upstream BSD-3-Clause-style terms.

Neither external checker source tree is bundled in this repository. The build scripts fetch and verify pinned upstream revisions. The author's original KBL code and proof data are covered by the path-scoped MIT and CC BY 4.0 grants in [LICENSE.md](LICENSE.md); those grants do not replace or modify either upstream license.

## Why historical manuscript and workflow files are retained

The original `evidence/paper/` manuscript and its bibliography retain older editorial metadata to preserve historical file identities. They are **not** the final preprint and should not be submitted or cited as such. Five historical workflow YAML files are preserved under `evidence/.github/workflows/` because the theorem trust-boundary auditor reads their static content. GitHub does not execute those files as root workflows in this nested location.

## Stable citation

The repository commit and `SHA256SUMS` establish exact versioned byte identity. A tagged release and any archive DOI should be cited **only if actually created**. There is no basis to claim an arXiv identifier or DOI before assignment.
