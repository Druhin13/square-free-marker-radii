# Reproducing the finite proof certificates

## Requirements

Use Linux (Ubuntu 24.04 is used by the GitHub Actions workflow), Python 3.9+ standard library, Bash, Git, a C11 compiler, and a C++17 compiler. The initial build requires network access to retrieve two pinned, independently developed proof checkers:

- [DRAT-trim](https://github.com/marijnheule/drat-trim), commit `effa1dcce85c878236f8313133dff1a2b766cd7c` (MIT).
- [CakeML cake_lpr](https://github.com/tanyongkiam/cake_lpr), commit `033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2` (upstream BSD-3-Clause-style terms).

The scripts build both under `evidence/.build/`. The generated checkers and reports are not part of the distributed source.

## Integrity verification

From the repository root:

```bash
sha256sum --check --strict SHA256SUMS
```

The certificate runner also checks all four proof registries and all 52 registered objects, before and after every verification family.

## Run the complete check

```bash
cd evidence
python3 -B reproduce.py --case all --report ../square-free-marker-all.json
```

Or run one case at a time:

```bash
python3 -B reproduce.py --case main      --report ../square-free-marker-main.json
python3 -B reproduce.py --case subgroups --report ../square-free-marker-subgroups.json
python3 -B reproduce.py --case swap      --report ../square-free-marker-swap.json
python3 -B reproduce.py --case double    --report ../square-free-marker-double.json
python3 -B reproduce.py --case exact     --report ../square-free-marker-exact.json
python3 -B reproduce.py --case trust     --report ../square-free-marker-trust.json
python3 -B reproduce.py --case lrat      --report ../square-free-marker-lrat.json
```

The report destination must not already exist. Each command is non-destructive to the checked-in certificate data.

| Case | Scope |
| --- | --- |
| `main` | Unrestricted finite constraints and full-symmetry source checks |
| `subgroups` | Subgroup obstruction certificates and refutations |
| `swap` | One-transposition-invariant radius-five marker rule |
| `double` | Double-transposition-invariant radius-five marker rule |
| `exact` | Higher-radius marker tables, four-cycle obstruction, and stabilizers |
| `trust` | Source-language sanity checks, mutation controls, verifier entry-point audit |
| `lrat` | Secondary independent LRAT replay of designated refutations |

### Observed runtime on a hosted Linux runner

The following values are measured **proof-command wall times** from one
successful seven-family reproduction on an Ubuntu 24.04 GitHub-hosted runner
(20 November 2026). They exclude job setup, checkout, and dependency installation.
They are observations, not performance guarantees or time limits:

| Family | Observed proof-command duration |
| --- | ---: |
| `main` | 52 s |
| `subgroups` | 34 s |
| `swap` | 94 s |
| `double` | 121 s |
| `exact` | 27 s |
| `trust` | 5 s |
| `lrat` | 13 s |

The proof families can run independently and in parallel. Allow additional time
for downloading and compiling the pinned checkers on a fresh system. Peak RAM
usage was not recorded for these runs, so no unsupported minimum-memory claim is
made. The GitHub Actions workflow defines a 50-minute timeout per family.

### Test from a real Git checkout

The tests work both on a standalone distribution tree and in a normal Git
checkout containing a root `.git` directory:

```bash
cd evidence
python3 -B -m unittest discover -s tests -v
```

To validate an exported ZIP **separately**, without extracting it or confusing
a working Git checkout with distributed contents:

```bash
cd ..  # return from evidence/ to the repository root
python3 -B evidence/tools/verify_distribution_archive.py /path/to/evidence.zip
```

Run the ZIP command from the repository root. It checks the archive member
paths, embedded Git metadata, file checksums, proof-object count, and workflow
allowlist. It does not require or modify Git metadata.

## Supplementary radius-four source-certificate checks

From the `evidence/` directory, the two independent clause-extension
checks can also be run separately against files included in this repository:

```bash
python3 -B -m scripts.audit_m3_r4_easy_core_independent
python3 -B -m scripts.audit_m3_r4_remaining_core_independent
```

These check source-factor realizations, **not** UNSAT by themselves.
For the complete radius-four result including the DRAT refutation, run:

```bash
bash tools/build_drat_trim.sh  # only if not already built
python3 -B -m scripts.verify_m3_radius4_lower_bound \
  --checker .build/drat-trim/drat-trim
```

The optional `audit_m3_r4_violation_extensions_independent` module audits
additional solver-experiment manifests that are **not** included here. It
requires explicit `--source` and `--candidates` inputs; it is not needed
for any of the seven supported certificate families. Other component-level
scripts may rely on paths supplied by the top-level reproduction driver.
For supported, complete checks, use `reproduce.py` as documented above.

## Scientific scope

These programs verify finite computational obligations. The classical Hall–Thue and two-sided separator/extension theorems are mathematical arguments, rather than mechanically formalized theorems in this codebase. `PROVENANCE.md` describes the trust boundaries and the exact certificate inventory.

## Optional fresh solver replays

The `evidence/scripts/replay_c03_*.py` scripts reproduce four additional negative and three positive solver-generation experiments. Their recorded measurements appear in `evidence/benchmarks/fresh-search-results.json`; timings from heterogeneous CPUs must not be interpreted as controlled comparisons or original discovery timings.

For these optional experiments, use Ubuntu 24.04 with CaDiCaL package `1.7.4-1` (the binary reports version 1.7.3), `/usr/bin/time`, `taskset`, and the pinned DRAT-trim checker. From the `evidence` directory:

```bash
sudo apt-get update
sudo apt-get install -y cadical=1.7.4-1 time
bash tools/build_drat_trim.sh
for c in r4 c3 normal-v4 intransitive-v4; do
  python3 -B -m scripts.replay_c03_solver_metadata --case "$c" \
    --solver /usr/bin/cadical --checker .build/drat-trim/drat-trim \
    --report "../fresh-unsat-${c}.json"
done
for c in swap double; do
  python3 -B -m scripts.replay_c03_positive_generation --case "$c" \
    --solver /usr/bin/cadical --report "../fresh-sat-${c}.json"
done
python3 -B -m scripts.replay_c03_unrestricted_r5_generation \
  --solver /usr/bin/cadical --report ../fresh-sat-unrestricted.json
```

Generated solver files are temporary and are checked by independent semantic validators. The reproduced verification leaves all registered certificate objects in `evidence/proofs/` unchanged.
