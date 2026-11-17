# Exact Marker Radii on the Quaternary Square-Free Shift under Alphabet Symmetry

**Computational proof certificates and independent verifiers accompanying Druhin Tarafder's manuscript.**

This is the public companion **evidence repository**, not the private research/development workspace. It makes the finite evidence for a fixed mathematical theorem independently checkable; it does not claim to formalize all infinite-word mathematics.

## The result

For the bi-infinite quaternary square-free shift, consider a Boolean sliding-block marker rule with separation at least three and covering distance at most two. The optimal symmetric input radius is **5** if the input alphabet-invariance subgroup has order at most two, **6** for larger subgroups without a four-cycle, and **7** for subgroups containing a four-cycle. In particular, the unrestricted optimum is 5 and the fully alphabet-symmetric optimum is 7. The 30 subgroups split 10 / 13 / 7 across these radii.

These are exact results only for the stated four-letter and marker parameters, not an all-parameter classification.

## Verify from a fresh checkout

Requirements: Linux; Python 3.9+ (standard library); Bash; Git; C11 and C++17 compilers. The initial checker builds fetch and pin third-party source revisions.

```sh
git clone https://github.com/Druhin13/square-free-marker-radii.git
cd square-free-marker-radii
sha256sum -c SHA256SUMS
cd evidence
python3 -B reproduce.py --case all --report ../kbl-reproduction-report.json
```

See [REPRODUCING.md](REPRODUCING.md) for separate case-by-case commands and prerequisites. The portable runner checks all **52 registered original proof objects** before and after the verification families.

## What's here

| Path | Purpose |
| --- | --- |
| `evidence/proofs/` | The 52 byte-identical original proof and witness objects |
| `evidence/artifacts/` | Four original SHA-256 proof registries |
| `evidence/scripts/`, `evidence/tools/`, `evidence/tests/` | Original computation, proof-checking, and mathematical regression code |
| `evidence/paper/` | **Historical, pinned manuscript sources only — not the current preprint** |
| `evidence/.github/workflows/` | Five **inert historical workflow files**, retained as inputs for the theorem trust auditor |
| `REPRODUCING.md` | How to rerun the seven proof families |
| `PROVENANCE.md` | Source scope, independent checkers, trust boundaries |
| `.github/workflows/verify-evidence.yml` | Read-only public CI: SHA-256 audit plus all seven proof families |
| `evidence/benchmarks/fresh-search-results.json` | Compact, verified measurements for four new UNSAT and three new SAT searches |
| `evidence/scripts/replay_c03_*.py` | Optional scripts to redo those fresh controlled searches |
| `SHA256SUMS` | Content hashes for all other files in this package |

### Critical scientific boundary

Finite SAT/DRAT/LRAT refutations, constructive marker tables, named-word constraints, and file identities are independently checked. Classical Hall–Thue infinite-word facts and the handwritten separator/finite-to-bi-infinite extension argument are **not machine-formalized**. Independent mathematical proof reading remains welcome.

The historical `evidence/paper/` pair has older author metadata because its bytes belong to the immutable computational provenance; do not submit or cite it as the current manuscript. The final author manuscript is separately maintained for arXiv.

## Attribution, licenses and citations

See [PROVENANCE.md](PROVENANCE.md) for the third-party DRAT-trim and CakeML checker revisions; those tools are fetched rather than redistributed. Use [CITATION.cff](CITATION.cff) to cite the evidence repository's exact revision. Do not infer a DOI or arXiv identifier until an actual public record exists.

## Licensing

The author's original **verification software and scripts** are licensed under the [MIT License](LICENSE-MIT.txt). Original **mathematical certificates, research datasets, documentation and LaTeX/manuscript sources** are licensed under [Creative Commons Attribution 4.0 International](LICENSE-CC-BY-4.0.md). The exact path-by-path scope, copyright notices and exceptions are described in [LICENSE.md](LICENSE.md).

The public CI runs the seven proof families in separate Ubuntu 24.04 jobs using read-only GitHub permissions; only this intentionally authored root workflow is executable. The historical theorem workflow contracts remain nested and inert.

The two independent external checkers are **not bundled**; their original licenses remain with their upstream authors. No blanket license is applied to third-party works cited by the manuscript.

For scientific use, cite the **exact Git commit or tagged release** you actually checked, together with the manuscript once it has been posted. This repository does not claim an unassigned arXiv identifier or DOI.
