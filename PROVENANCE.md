# Evidence provenance and verification boundaries

## Certificate inventory

The repository distributes 52 fixed proof and witness objects totaling **115,721,014 bytes**. Their registered paths, sizes, and cryptographic identities are checked before every verification family:

| Registry | Objects | Identity |
| --- | ---: | --- |
| `evidence/artifacts/manifest.json` | 21 | SHA-256 and byte count |
| `evidence/artifacts/subgroup-manifest.json` | 23 | Git blob SHA-1 and byte count |
| `evidence/artifacts/subgroup-positive-manifest.json` | 3 | Git blob SHA-1 and byte count |
| `evidence/artifacts/exact-symmetry-addendum-manifest.json` | 5 | SHA-256 and byte count |

The four registries identify the **authoritative distributed certificate versions**.
SHA-256 or Git-blob identities, byte counts, and `SHA256SUMS` allow independent
verification of the published package. Every reproduction family checks that
the registered objects remain unchanged **during verification**.

### Byte preservation and normalized metadata

The DIMACS CNF instances, DRAT proofs, and SAT-model text files retain
their verified bytes. Supporting JSON audit reports use descriptive
certificate paths and corresponding input digests. These naming and
metadata changes do not affect the underlying clauses, source words,
marker assignments, proof conclusions, or mathematical interpretation.
The four registries and root `SHA256SUMS` identify the exact files
distributed in this release.

## What is independently checked

The verification programs check finite packing and covering clauses, named source factors and source witnesses, constructive marker tables, subgroup/stabilizer calculations, propositional refutations, and selected LRAT checking obligations. The `trust` family includes adversarial mutations to verify that selected malformed source certificates are rejected for semantic reasons.

The computational checks do **not** formalize the classical infinitude and recurrence properties of Hall–Thue square-free words, the handwritten separator/extension lemmas, or broader priority claims. Interpreting the verified finite contradictions for bi-infinite square-free configurations uses the mathematical arguments in the accompanying manuscript.

## Third-party proof checkers

- [DRAT-trim](https://github.com/marijnheule/drat-trim), pinned at `effa1dcce85c878236f8313133dff1a2b766cd7c` (upstream MIT).
- [CakeML cake_lpr](https://github.com/tanyongkiam/cake_lpr), pinned at `033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2` (upstream BSD-3-Clause-style terms).

Both projects are retrieved from their upstream source repositories by reproducible build scripts. Their sources, binaries, and third-party licenses are not redistributed here. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for additional attribution and pinned upstream license links.

## Controlled solver experiments

`evidence/benchmarks/fresh-search-results.json` records additional controlled solver runs, including input digests, model or refutation output digests, solver identity, and execution resources. These are reproduction experiments rather than recoveries of the original proof-discovery timings. Different machines were used, so their running times do not support a controlled performance comparison.

## Versioning

Use the Git commit or release tag to identify the exact evidence version used. The SHA-256 manifest and four proof registries provide content-level verification independent of citations or a future archive DOI.
