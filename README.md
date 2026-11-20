# Exact Marker Radii on the Quaternary Square-Free Shift under Alphabet Symmetry

Reproducible computational evidence for the exact marker-radius classification established by Druhin Tarafder.

## Result

Let X be the bi-infinite square-free shift over an alphabet of four letters. Consider shift-equivariant Boolean marker rules that select sites at least three positions apart while placing a marker within distance two of every site. For alphabet-permutation invariance under H ≤ S₄, the optimal symmetric coding radius is:

| Alphabet-invariance subgroup H | Minimum radius | Number of subgroups |
| --- | ---: | ---: |
| Order at most two | **5** | 10 |
| Order greater than two; no four-cycle | **6** | 13 |
| Contains a four-cycle | **7** | 7 |

Consequently, the unrestricted optimum is 5 and the fully S₄-invariant optimum is 7. These values apply to the specified alphabet and marker parameters; they are not claimed for other parameter choices.

## Paper

This evidence repository accompanies *Exact Marker Radii on the Quaternary
Square-Free Shift under Alphabet Symmetry* by Druhin Tarafder. The complete
mathematical argument is in the manuscript, which is not distributed here.
A permanent public manuscript link will be provided when the paper is posted;
no arXiv identifier or DOI is asserted without an existing public record.

## Reproduce the finite certificates

A Linux environment with Python 3.9+, Bash, Git, C11 and C++17 compilers is recommended. The independent DRAT-trim and CakeML LRAT checkers are built from pinned upstream revisions; network access is needed for their initial retrieval.

```bash
git clone https://github.com/Druhin13/square-free-marker-radii.git
cd square-free-marker-radii
sha256sum --check --strict SHA256SUMS
cd evidence
python3 -B reproduce.py --case all --report ../kbl-all.json
```

The verification runs seven families (`main`, `subgroups`, `swap`, `double`, `exact`, `trust`, `lrat`). All 52 registered certificate objects are checked against their published content hashes before and after verification. See [REPRODUCING.md](REPRODUCING.md) for individual commands, external dependencies, runtime considerations, and additional controlled solver experiments.

## Repository contents

| Location | Description |
| --- | --- |
| [`evidence/proofs/`](evidence/proofs/) | 52 registered certificate and witness objects (115,720,144 bytes) |
| [`evidence/artifacts/`](evidence/artifacts/) | Four proof registries, with exact source-object digests |
| [`evidence/reproduce.py`](evidence/reproduce.py) | Standalone seven-family reproduction entry point |
| [`evidence/tools/`](evidence/tools/) | Independent verification and checker build tools |
| [`evidence/scripts/`](evidence/scripts/) | Certificate-generation and mathematical audit programs |
| [`evidence/tests/`](evidence/tests/) | Regression and adversarial tests |
| [`evidence/benchmarks/`](evidence/benchmarks/) | Reproducible measurements from later controlled solver runs |
| [`SHA256SUMS`](SHA256SUMS) | SHA-256 digests for all other distributed files |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | Upstream checker revisions, authors, and licensing |
| [`evidence/tools/verify_distribution_archive.py`](evidence/tools/verify_distribution_archive.py) | Optional standalone ZIP integrity audit (not a checkout test) |

The accompanying manuscript is maintained separately and is not part of this evidence-only release. The repository contains neither a purported final preprint nor a substitute for the manuscript's mathematical proofs.

## Verification scope

The software checks the finite proof obligations: certified UNSAT cores and source witnesses, independently validated marker assignments, finite-source packing/covering constraints, alphabet subgroups, and selected DRAT/LRAT refutations. Classical Hall–Thue results and the two-sided separator/extension lemmas remain mathematical arguments; they are **not** mechanically formalized by this repository. See [PROVENANCE.md](PROVENANCE.md) for precise evidence boundaries.

## Citation and licensing

Credit Druhin Tarafder and cite the exact commit or release checked, alongside the manuscript once available. Citation metadata is provided in [CITATION.cff](CITATION.cff). This repository does not claim an unassigned DOI or arXiv identifier.

Original verification software is licensed under MIT. Original research data, mathematical certificates, and documentation are licensed under CC BY 4.0. Upstream checker licenses are preserved; see [LICENSE.md](LICENSE.md) for the file-by-file scope and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for dependency attribution.
