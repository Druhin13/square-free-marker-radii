# Reproduce the seven finite-certificate proof families

This document accompanies the public KBL evidence package. The runner operates entirely inside `evidence/` and does not require the private research repository, private CI, or unpublished development history.

## Prerequisites

Use Linux, Python 3.9+ (standard library), Bash, Git, GCC or other C11/C++17 compilers and outbound network access on the **first** checker build. It downloads the following independently developed tools at exact source commits, under their original licenses:

- [DRAT-trim](https://github.com/marijnheule/drat-trim) at `effa1dcce85c878236f8313133dff1a2b766cd7c` (MIT).
- [CakeML cake_lpr](https://github.com/tanyongkiam/cake_lpr) at `033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2` (BSD-3-Clause-style upstream terms).

Those tools are **not bundled**. The build scripts place generated objects under `evidence/.build/` and validate the requested revisions.

## Content integrity

At the repository root, run `sha256sum -c SHA256SUMS` before and after reproduction. The four original artifact registries are additionally verified by the portable runner. Every listed digest refers to an exact file, not merely an equivalent SAT instance.

## Individual verification commands

From the `evidence` directory:

```sh
python3 -B reproduce.py --case main      --report ../kbl-main.json
python3 -B reproduce.py --case subgroups --report ../kbl-subgroups.json
python3 -B reproduce.py --case swap      --report ../kbl-swap.json
python3 -B reproduce.py --case double    --report ../kbl-double.json
python3 -B reproduce.py --case exact     --report ../kbl-exact.json
python3 -B reproduce.py --case trust     --report ../kbl-trust.json
python3 -B reproduce.py --case lrat      --report ../kbl-lrat.json
```

Or invoke `python3 -B reproduce.py --case all --report ../kbl-all.json`. The report destination must not already exist. Do not commit build products or verification report files.

| Case | Verified scope |
| --- | --- |
| `main` | Original unrestricted/full-symmetry finite certificate and named-source checks |
| `subgroups` | Negative subgroup source certificates and associated refutations |
| `swap` | Radius-five marker assignment invariant under one transposition |
| `double` | Radius-five marker assignment invariant under a double transposition |
| `exact` | Higher-radius constructive marker tables, four-cycle obstruction, exact stabilizers |
| `trust` | Source-language assumptions, adversarial tests and historical workflow-contract assertions |
| `lrat` | Specified refutations replayed through independently built CakeML LRAT checking |

The seven cases were previously checked independently in clean source-only CI environments. Individual cases can be compute-intensive; `all` reruns the whole sequence. The runner checks **52 original proof objects totaling 115,720,432 bytes**, covering the 21 + 23 + 3 + 5 original object registries, before and after verification.

## Boundaries and historical context

The evidence proves the finite computational obligations at the stated scope. The Hall–Thue infinite-word facts and handwritten separator lemmas are mathematical premises, not theorems mechanically certified by these scripts. Fresh solver-generation benchmarks in the manuscript are separate from this certificate-checking protocol, and historical original search settings/timings were not recovered.

`evidence/paper/` contains the **historical pinned baseline**, not the current authored manuscript. The five historical workflow YAML files under `evidence/.github/workflows/` are inert because they are nested beneath the root; they remain needed as read-only inputs for the trust checker. Do not move them to a root `.github/workflows/` directory without a new security review.

## Optional controlled fresh solver-generation replays

The seven historically separate **new** experiments reported in the paper have five supplementary Python scripts under `evidence/scripts/` and a compact record at `evidence/benchmarks/fresh-search-results.json`. They are distinct from the seven finite-certificate verification families above. Their measured times arose on heterogeneous GitHub Actions CPUs and cannot be compared as a controlled benchmark or treated as recovered original discovery timings.

Use Ubuntu 24.04 with the exact packaged CaDiCaL `1.7.4-1` (self-reported 1.7.3), `/usr/bin/time`, `taskset`, and the pinned DRAT-trim checker; the scripts strictly verify the executable identity and their SHA-pinned source CNFs. From `evidence/` run:

```sh
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

New solver models and DRAT traces are deliberately disposable; the independent verifiers check their semantic correctness. The historical original certificates under `evidence/proofs/` remain unchanged. CPU, memory and timeout limits depend on the machine.
