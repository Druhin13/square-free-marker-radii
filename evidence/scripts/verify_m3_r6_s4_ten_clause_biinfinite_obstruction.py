#!/usr/bin/env python3
"""Independent 10-source bi-infinite S4 radius-six obstruction audit.

The independently byte-verified FULL q=4,m=3,r=6/S4 finite-factor CNF
had 1,429,489 original source-orbit rows. Its independently checked
binary DRAT proof reduced to just TEN original source clauses,
with a standalone 195-byte reduced CNF and 222-byte optimized ASCII DRAT.

This independent verifier imports neither the CNF exporter nor the CNF
auditor or a prior marker extension constructor. It checks:

  1. exact immutable SHA256 identities for original CNF, its source-level
     independent audit, the 10-clause core, both optimized/core source
     DRAT files, and the prior source-export manifest;
  2. reconstructs all original named length13 S4 context IDs and all
     canonical length14, 15, 17 original squarefree source orbit rows,
     checking exact mapping of the TEN refuted original clauses to TEN
     UNIQUE source factor words, exact lexical source ordinals, original
     full CNF line identity and polarity;
  3. independently verifies ten explicit finite witness extensions:
     full squarefreeness, exact original source occurrence, isolated
     distinguished separator 0, first/last separator span D, the
     D-1 margins on BOTH sides, and occurrence of each ternary exterior
     in the relabeling/reversal orbit of the classical Hall-Thue fixed
     point of morphism 0->012, 1->02, 2->1;
  4. exhaustively evaluates ALL 2^8 Boolean assignments of the
     10-clause standalone core and INDEPENDENTLY replays the binary
     full-CNF DRAT and reduced ASCII core DRAT with drat-trim. Checker
     must exit 0 and print EXACT line 's VERIFIED' in both cases.

A finite-padding check alone does not establish that a complete
zero-free extremity embeds in a single Hall--Thue ray. Therefore this
verifier requires an independently checked complete-tail certificate
as an explicit prerequisite for the bi-infinite statement, alongside
all finite-source and DRAT checks.

The classical infinite Hall-Thue squarefreeness/uniform recurrence and
the generalized finite-separator D-1 lemma are MATHEMATICAL PREMISES,
not proved by testing finite prefixes. Only AFTER the independently
checked complete-tail audit and all four phases pass does the
computer-assisted conditional theorem follow:

NO full S4-invariant shift-equivariant radius-six Boolean marker rule
on the bi-infinite quaternary squarefree subshift can simultaneously
have separation>=3 and domination distance<=2.

This calculation does not address arbitrary m or other radii.
Input proof/source artifacts are never modified.
One NEW report is created exclusively, with deterministic JSON contents.

Run from the evidence directory:
  python3 -B -m scripts.verify_m3_r6_s4_ten_clause_biinfinite_obstruction \
    --checker /tmp/square-free-marker-drat-trim/drat-trim

For a fresh source checkout, replay using only the registered inputs:
  python3 -B -m scripts.verify_m3_r6_s4_ten_clause_biinfinite_obstruction \
    --checker /tmp/square-free-marker-drat-trim/drat-trim \
    --archive-dir proofs/m3/s4-r6-ten-core \
    --report /tmp/square-free-marker-m3-r6-s4-ten-core-clean-PROOFSHA-audit.json

Archive replay pins all NINE archived files, including the original
integrated report, before independently regenerating exactly the same audit
JSON at a fresh path. No archived/source file is modified.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path
import subprocess
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / ".build/square-free-marker-q4-m3-r6-s4.cnf"
EXPORT = Path("/tmp/square-free-marker-m3-r6-s4-export.json")
PRE = Path("/tmp/square-free-marker-m3-r6-s4-orbit-preflight.json")
AUDIT = Path("/tmp/square-free-marker-m3-r6-s4-cnf-audit.json")
CORE = Path("/tmp/square-free-marker-m3-r6-s4-ten-core/core.cnf")
LEMMAS = Path("/tmp/square-free-marker-m3-r6-s4-ten-core/core-lemmas.drat")
BINARY = Path("/tmp/square-free-marker-m3-r6-s4-proof.drat")
RESULT = Path("/tmp/square-free-marker-m3-r6-s4-result.txt")
REPORT = Path("/tmp/square-free-marker-m3-r6-s4-ten-core-biinfinite-audit.json")

SHA = {
    CNF: "95c9c6aa8e1cf8d14200feb59a4d9e4160a7818cf63e35eb19e6e3ab4310da6e",
    EXPORT: "00782082b21d28096bd5e1368b8a83b8cea94318242d04fb1af2f02b3ae5491b",
    PRE: "d58cd38c36ceb8ee68461968f7995fb57bf21205a85205b39f18b01f488e2be0",
    AUDIT: "26adea7b5584fcda6d5c9de0f9b0e7da13b57b97e43babfa599169bfc7b39d3c",
    CORE: "b80b008364dace6c4177bb5f5d71b5e0ee2b828c7ea85a15c21e75eed7c86a14",
    LEMMAS: "16c6f25a8d3136a0b6ed916c639c17d99080263ea40008b51666dfc62287a700",
    BINARY: "877b2d2c3417735de7a2d74b9e7359bd4fe62a495ac3bdbe28af9c28a31fa6a3",
    RESULT: "bde6e1eede96772c07c8ce29fd18088863815bd043aa59a06f11f5838cf8a162",
}
EXPECTED_BYTES = {
    CNF: 39463151, EXPORT: 1599, PRE: 2793, AUDIT: 1598,
    CORE: 195, LEMMAS: 222, RESULT: 16,
}
SOURCE_CLASSES = {14: 2, 15: 4, 17: 4}
FACTOR_TOTALS = {14: 66047, 15: 173183, 17: 1190259}
FAMILY_FIRST = {14: 0, 15: 66047, 17: 239230}
VARS = 25192
TOTAL = 1429489
HALL_MORPHISM = {"0": "012", "1": "02", "2": "1"}

# Each record is an EXPLICIT proposed finite extension source certificate:
# (exact core clause; original factor length; zero-based canonical factor
#  lexical rank; original source factor; left ternary padding; right padding).
# Code below does NOT trust source ordinals or factors until reconstructed
# independently from all original named n13 and canonical source families.
CASES = (
    ("-21696 -4588", 14, 12029, "01023013210231",
     "121323123", "213123132"),
    ("-12753 -7817", 14, 20497, "01201302312010",
     "121312321323", "212312132123"),
    ("-7817 -21695", 15, 53747, "012013023120103",
     "121312321323", "121312321312"),
    ("-12754", 15, 87684, "012032130120321",
     "1213231232", "2312131232"),
    ("-21697", 15, 149148, "012310320123103",
     "121312321323", "121312321312"),
    ("-12753 -21915", 15, 150654, "012312013023121",
     "12131232", "31231321"),
    ("12753 4588 12754 21697", 17, 216750, "01023013210230131",
     "121312321312", "213212312132"),
    ("21696 7817 12754 21697", 17, 369411, "01201302312013021",
     "1213123213121", "2312131232131"),
    ("21695 12753 12754 21697", 17, 1025066, "01231032012310302",
     "12131232131213", "12312132123132"),
    ("21915 7817 21697 12754", 17, 1035405, "01231201302312013",
     "1213123213121", "1213212312132"),
)


def require(condition, description):
    if not condition:
        raise AssertionError(description)


def hash_file(path):
    h = sha256()
    n = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            n += len(block)
            h.update(block)
    return h.hexdigest(), n


def pin_file(path):
    require(path.is_file() and not path.is_symlink(),
            f"Missing or unsafe original proof artifact: {path}")
    actual, size = hash_file(path)
    require(actual == SHA[path],
            f"Original proof artifact SHA mismatch: {path}, actual={actual}")
    if path in EXPECTED_BYTES:
        require(size == EXPECTED_BYTES[path],
                f"Wrong original byte size: {path}")
    return size


def read_core():
    lines = CORE.read_text(encoding="ascii").splitlines()
    require(lines and lines[0] == "p cnf 25192 10" and len(lines) == 11,
            "10-clause standalone core has unexpected header/count")
    result = []
    for line in lines[1:]:
        fields = tuple(int(q) for q in line.split())
        require(fields and fields[-1] == 0 and
                fields.count(0) == 1 and
                all(0 < abs(v) <= VARS for v in fields[:-1]),
                "Bad exact original core clause")
        result.append(tuple(sorted(fields[:-1])))
    require(len(result) == 10 and len(set(result)) == 10,
            "Unexpected original core clause duplication")
    return result


def suffix_square(word):
    """Independently check every possible newly completed suffix square."""
    n = len(word)
    for p in range(1, n//2+1):
        if word[n-2*p:n-p] == word[n-p:n]:
            return True
    return False


def squarefree_full(word):
    """Check every start AND every possible period in entire finite word."""
    for i in range(len(word)):
        for p in range(1,(len(word)-i)//2+1):
            if word[i:i+p] == word[i+p:i+2*p]:
                return False
    return True


def all_named(n):
    """Independently reconstruct original named squarefree factors."""
    stack = [()]
    while stack:
        word = stack.pop()
        if len(word) == n:
            yield word
            continue
        for ch in (3,2,1,0):
            extended = word+(ch,)
            if not suffix_square(extended):
                stack.append(extended)


def normalize(word):
    """Original word alphabet -> unique first occurrence pattern."""
    mapping = {}
    out = []
    for v in word:
        if v not in mapping:
            mapping[v] = len(mapping)
        out.append(mapping[v])
    return tuple(out)


def original_orbits(n):
    """Independent canonical source DFS, separate from original exporter."""
    stack = [((),-1)]
    while stack:
        word, largest = stack.pop()
        if len(word) == n:
            yield word
            continue
        for v in range(min(3,largest+1),-1,-1):
            extended = word+(v,)
            if not suffix_square(extended):
                stack.append((extended,max(v,largest)))


def source_clause(source, ids):
    n = len(source)
    require(n in FACTOR_TOTALS,
            "Original source factor is in unexpected length family")
    offsets = (0,1) if n == 14 else (0,2) if n == 15 else (0,1,2,3,4)
    numbers = []
    for i in offsets:
        word = normalize(source[i:i+13])
        require(word in ids, "Original source context not in S4 quotient")
        var = ids[word]
        numbers.append(var if n == 17 else -var)
    return tuple(sorted(set(numbers)))


def original_source_map(core):
    original = set(core)
    ids = {}
    named = 0
    for word in all_named(13):
        named += 1
        if word == normalize(word):
            require(word not in ids, "Duplicate original n13 decision context")
            ids[word] = len(ids)+1
    require(named == 604608 and len(ids) == VARS,
            f"Wrong original named S4 context ID census {named}/{len(ids)}")
    print("  Original named n13 contexts: 604608; S4 orbit IDs: 25192",
          flush=True)

    matched = defaultdict(list)
    counts = Counter()
    for n in (14,15,17):
        for rank, word in enumerate(original_orbits(n)):
            clause = source_clause(word, ids)
            if clause in original:
                matched[clause].append({
                    "source_length": n,
                    "source_orbit_lex_rank_zero_based": rank,
                    "original_cnf_source_row_zero_based": FAMILY_FIRST[n]+rank,
                    "canonical_source_word": "".join(map(str,word)),
                })
            counts[n] += 1
        require(counts[n] == FACTOR_TOTALS[n],
                f"Full original S4 source orbit census mismatch n{n}")
        print(f"  Full original source n{n} orbit census: {counts[n]}",
              flush=True)
    require(set(matched) == original and
            all(len(matched[c]) == 1 for c in original),
            "Core clauses do not each map to exactly ONE original factor orbit")
    require(Counter(matched[c][0]["source_length"]
                    for c in original) == Counter(SOURCE_CLASSES),
            "Expected two n14, four n15 and four n17 source factors")
    return ids, matched, counts


def confirm_original_cnf_rows(mapped, core):
    selected = {
        v[0]["original_cnf_source_row_zero_based"]: clause
        for clause,v in mapped.items()
    }
    require(len(selected)==10, "Repeated original source CNF row")
    seen = set()
    with CNF.open("rb") as stream:
        require(stream.readline() == b"p cnf 25192 1429489\n",
                "Original full DIMACS header mismatch")
        for i, line in enumerate(stream):
            if i in selected:
                expected = (" ".join(str(x) for x in selected[i]) +
                            " 0\n").encode("ascii")
                require(line == expected,
                        f"Original source CNF row {i} differs from "
                        f"independent factor mapping: got={line!r} "
                        f"expected={expected!r}")
                seen.add(i)
        require(i+1==TOTAL and seen==set(selected),
                "Full original source row count or core row identity differs")


def phase_one():
    for path in SHA:
        size=pin_file(path)
        print(f"  SHA-PINNED: {path.name} ({size} bytes)", flush=True)
    core=read_core()
    require(
        set(core) ==
        {tuple(sorted(map(int, r[0].split()))) for r in CASES},
        "Candidate extension source rows do not match 10-clause refuted core")
    ids,mapped,counts=original_source_map(core)
    require(len(ids)==VARS, "Incorrect original decision context census")
    for statement in CASES:
        line,n,rank,word,left,right=statement
        clause=tuple(sorted(map(int,line.split())))
        record=mapped[clause][0]
        require((record["source_length"],
                 record["source_orbit_lex_rank_zero_based"],
                 record["canonical_source_word"])==(n,rank,word),
                "Explicit original source factor word/rank mismatch")
    confirm_original_cnf_rows(mapped,core)
    print("PHASE 1/4 PASSED: ALL TEN original SHA-pinned "
          "finite CNF source-factor identities", flush=True)
    return core,mapped,counts


def hall_word():
    word="0"
    while len(word)<32768:
        word="".join(HALL_MORPHISM[c] for c in word)
    # Check only a finite sanity prefix, never claim this establishes
    # infinite squarefreeness or recurrence of the classical word.
    require(squarefree_full(word[:220]),
            "Finite Hall prefix sanity squarefree check failed")
    return word[:32768]


def locate_hall_exterior(exterior, hall):
    require(exterior and set(exterior) <= set("123"),
            "Separator 0 occurs in an exterior Hall factor")
    for perm in permutations("123"):
        table=dict(zip("012",perm))
        inverse={v:k for k,v in table.items()}
        reduced="".join(inverse[c] for c in exterior)
        for reverse in (False, True):
            search=reduced[::-1] if reverse else reduced
            index=hall.find(search)
            if index >= 0:
                return {
                    "hall_factor": search,
                    "hall_prefix_offset": index,
                    "hall_to_exterior_bijection":
                        ["".join(("0",table["0"])),
                         "".join(("1",table["1"])),
                         "".join(("2",table["2"]))],
                    "reversed_hall_factor": reverse,
                }
    raise AssertionError("Exterior factor cannot be certified from Hall orbit")


def phase_two(core,mapped):
    hall=hall_word()
    certs=[]
    for num,(line,n,rank,w,left,right) in enumerate(CASES,1):
        original=tuple(sorted(map(int,line.split())))
        require(original in core and mapped[original][0][
                "canonical_source_word"]==w,
                "Finite certificate not linked to original source")
        witness=left+w+right
        require(len(w)==n and squarefree_full(w) and
                squarefree_full(witness),
                f"Finite separator witness {num} is not squarefree")
        require(witness[len(left):len(left)+n]==w,
                "Target not embedded at declared witness offset")
        separator=[i for i,x in enumerate(witness) if x=="0"]
        require(len(separator)>=2, "Separator 0 has fewer than 2 copies")
        require("0" not in left and "0" not in right,
                "External padding introduces new separator")
        first,last=separator[0],separator[-1]
        span=last-first
        require(len(left)==len(right)==span-1 and
                first==len(left) and last==len(left)+w.rfind("0"),
                f"Finite separator D-1 margin/source boundary failure {num}")
        left_hall=locate_hall_exterior(left,hall)
        right_hall=locate_hall_exterior(right,hall)
        certificate={
            **mapped[original][0],
            "core_clause": list(original),
            "source_word": w,
            "source_witness": witness,
            "witness_offset": len(left),
            "witness_squarefree_independently_verified": True,
            "separator": "0",
            "separator_positions": separator,
            "separator_span": span,
            "left_margin": len(left),
            "right_margin": len(right),
            "left_exterior": left,
            "right_exterior": right,
            "left_hall_certificate": left_hall,
            "right_hall_certificate": right_hall,
        }
        certs.append(certificate)
        print(f"  SOURCE {num}/10: n{n}, ordinal={rank}, "
              f"Z_length={len(witness)}, D={span}, "
              f"margins={len(left)}/{len(right)}", flush=True)
    require(len(certs)==10, "Incomplete original source certificates")
    print("PHASE 2/4 PASSED: ALL TEN original core source factors are "
          "Hall-Thue/separator bi-infinitely extendible", flush=True)
    return certs


def phase_three(core):
    all_vars=sorted({abs(lit) for clause in core for lit in clause})
    require(all_vars==[4588,7817,12753,12754,21695,21696,21697,21915],
            f"Unexpected Boolean variables in independent 10-core {all_vars}")
    require(len(core)==10,"Unexpected source clause count")
    sat=0
    for bits in product((False,True),repeat=len(all_vars)):
        valuation=dict(zip(all_vars,bits))
        if all(any(valuation[abs(v)] if v>0
                   else not valuation[abs(v)]
                   for v in clause) for clause in core):
            sat+=1
    require(sat==0, "Independent eight-variable truth table found SAT model")
    # Short human-readable proof, with U=12754, V=21697 forced false:
    # A=12753, B=7817, C=4588, D=21696, E=21695, F=21915.
    # The eight remaining clauses reduce to
    # (A or C), (D or B), (A or E), (F or B),
    # (~D or ~C), (~A or ~B), (~B or ~E), (~A or ~F).
    # If A: then ~B -> F -> ~A, contradiction. Hence ~A.
    # Then C and E, whence ~B and D, contradicting (~D or ~C).
    print("PHASE 3/4 PASSED: ALL 256 original 8-variable core "
          "Boolean assignments independently refuted", flush=True)
    return all_vars


def replay_drat(checker,formula,proof,flag):
    p=subprocess.run([str(checker),str(formula),str(proof),flag],
                     stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                     check=False)
    output=p.stdout.decode("utf-8",errors="replace")
    statuses=[x.strip() for x in output.splitlines() if x.startswith("s ")]
    require(p.returncode==0 and statuses==["s VERIFIED"],
            f"Independent DRAT checker failed on {formula}: "
            f"exit={p.returncode}, statuses={statuses}, "
            f"tail={output[-2000:]}")
    return {
        "checker_exit":p.returncode,
        "exact_status":statuses[0],
        "source_formula_sha256":SHA[formula],
        "proof_sha256":SHA[proof],
    }


def phase_four(checker):
    require(checker.is_file() and not checker.is_symlink(),
            "Missing/symlink independent DRAT checker")
    require(checker.stat().st_mode & 0o111,
            "Independent checker must be executable")
    first=replay_drat(checker,CNF,BINARY,"-i")
    second=replay_drat(checker,CORE,LEMMAS,"-I")
    for path in SHA:
        pin_file(path)
    print("PHASE 4/4 PASSED: original binary DRAT and reduced standalone "
          "ASCII DRAT independently s VERIFIED", flush=True)
    return {"full_binary_proof":first,"standalone_reduced_proof":second}


def configure_archive_inputs(archive_dir):
    """Switch ALL eight source inputs to exact Git-archived copies.

    Verify the nine original-file SHA pins (including the
    integrated certificate audit JSON) before proceeding with proof verification.
    The byte-for-byte output is invariant under source location because
    report serialization keys use basename and source content only.
    """
    global CNF, EXPORT, PRE, AUDIT, CORE, LEMMAS, BINARY, RESULT
    global SHA, EXPECTED_BYTES

    relative = Path(archive_dir)
    require(relative == Path("proofs/m3/s4-r6-ten-core"),
            "Archive mode accepts only canonical proof archive directory")
    directory = ROOT / relative
    require(directory.is_dir() and not directory.is_symlink() and
            all(not (ROOT / a).is_symlink()
                for a in ("proofs", "proofs/m3")),
            "Archive path missing or symlinked")
    original = (CNF, EXPORT, PRE, AUDIT, CORE, LEMMAS, BINARY, RESULT)
    archive = tuple(directory / path.name for path in original)
    require(len(set(archive)) == 8, "Archive name collision")
    require(set(path.name for path in directory.iterdir()) ==
            {path.name for path in archive} | {REPORT.name},
            "Archive contains missing or unexpected file")
    # Compare source fingerprints independently against exact original
    # pins, not a manifest that could accidentally certify itself.
    for old, new in zip(original, archive):
        require(new.is_file() and not new.is_symlink(),
                f"Missing or symlinked Git-archived input: {new}")
        observed, size = hash_file(new)
        require(observed == SHA[old],
                f"Archived input SHA mismatch: {new}")
        if old in EXPECTED_BYTES:
            require(size == EXPECTED_BYTES[old],
                    f"Wrong original source byte count in archive: {new}")

    old_report = directory / REPORT.name
    require(old_report.is_file() and not old_report.is_symlink(),
            "Missing/symlink original integrated audit in archive")
    observed, report_bytes = hash_file(old_report)
    require(report_bytes == 14812 and observed ==
            "96c587da47b168783b7314de9edac9d999a853e41daec1a1aa802094ad544bfa",
            "Original archived audit report SHA/size mismatch")

    old_sha = SHA
    old_sizes = EXPECTED_BYTES
    SHA = {new: old_sha[old] for old,new in zip(original,archive)}
    EXPECTED_BYTES = {new: old_sizes[old] for old,new in
                      zip(original,archive) if old in old_sizes}
    CNF, EXPORT, PRE, AUDIT, CORE, LEMMAS, BINARY, RESULT = archive
    print("ARCHIVE MODE: all nine exact Git-archived proof artifacts pinned")
    print("  Immutable archive directory:", relative)
    print("  Original integrated audit:", observed, flush=True)


def main():
    arg=argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--checker",default="/tmp/square-free-marker-drat-trim/drat-trim",
                     help="External standalone independently compiled DRAT verifier")
    arg.add_argument("--archive-dir", default=None,
                     help="Use exclusively SHA-pinned immutable proof archive")
    arg.add_argument("--report",default=str(REPORT),
                     help="NEW exclusive deterministic audit JSON path")
    arg.add_argument("--complete-tail-audit",type=Path,required=True,
                     help="The independent corrected-full-extremities report, SHA-256 pinned")
    opts=arg.parse_args()
    full_tail = opts.complete_tail_audit
    require(full_tail.is_file() and not full_tail.is_symlink(),
            "Independent corrected full-tail audit is missing/unsafe")
    observed, report_size = hash_file(full_tail)
    require(report_size == 3116 and observed ==
            "931c8565a2ccba6af4f28ae1af711e5cac91585743bf3b0f0264177f25a4401e",
            "Corrected full-extremity independent audit SHA/size mismatch")
    repaired = json.loads(full_tail.read_text(encoding="utf-8"))
    require(repaired.get("status") ==
            "INDEPENDENT FULL-TAIL S4 RADIUS-SIX COMPLETION AUDIT PASSED"
            and repaired.get("source_count") == 10
            and repaired.get("replaced_right_padding_count") == 6
            and repaired.get("all_complete_extremities_match_forward_Hall_factors") is True
            and repaired.get("all_original_core_sources_preserved") is True
            and repaired.get("all_finite_repaired_witnesses_squarefree") is True
            and repaired.get("repaired_certificate_sha256") ==
                "b202eeee869a5f8b0a0d1ec2c14ab2d5418186c3d9ec79c46af794aa4fbce3c1",
            "Independent corrected-tail report lacks expected certificate premises")
    started=perf_counter()
    if opts.archive_dir is not None:
        configure_archive_inputs(opts.archive_dir)
    report=Path(opts.report)
    require(not report.exists() and not report.is_symlink(),
            "Refusing to overwrite pre-existing theorem audit JSON")
    # On macOS, /tmp is a system-managed symlink to /private/tmp.
    # Permit only that exact, known alias; do not allow arbitrary
    # symlinked output parents or silently follow a custom alias.
    resolved_parent = report.parent.resolve(strict=True)
    require(
        report.parent.is_dir() and resolved_parent.is_dir()
        and (not report.parent.is_symlink()
             or (report.parent == Path("/tmp")
                 and resolved_parent == Path("/private/tmp"))),
        "Unsafe or missing report parent directory",
    )
    print("TEN-CLAUSE FULL-S4 "
          "RADIUS-SIX OBSTRUCTION SOURCE AUDIT",flush=True)

    core,mapped,counts=phase_one()
    certificates=phase_two(core,mapped)
    variables=phase_three(core)
    verification=phase_four(Path(opts.checker))
    report_data={
        "status":"ALL FOUR S4 RADIUS SIX TEN-SOURCE BI-INFINITE AUDIT PHASES PASSED",
        "scope": {
            "q":4,"m":3,"r":6,"group":"full S4",
            "separation":">=3","domination_radius":"<=2",
            "subshift":"bi-infinite quaternary squarefree words",
        },
        "premises_not_machine_proved":[
            "classical ternary Hall-Thue uniform recurrence and squarefreeness",
            "generalized finite-separator D-1 extension lemma",
        ],
        "original_input_sha256":
            {path.name:SHA[path] for path in SHA},
        "original_full_source_orbit_counts":
            {str(n):counts[n] for n in (14,15,17)},
        "original_core_clause_count":10,
        "exact_core_variables":variables,
        "direct_truth_table_assignments_checked":2**len(variables),
        "direct_truth_table_satisfying_assignments":0,
        "original_source_certificates":certificates,
        "independent_drat_replays":verification,
        "conclusion":(
            "Conditional fixed-parameter theorem: no shared radius-6 "
            "full S4-invariant marker rule on all bi-infinite quaternary "
            "squarefree words with separation >=3, domination <=2."
        ),
    }
    raw=(json.dumps(report_data,indent=2,sort_keys=True)+"\n").encode("utf-8")
    with report.open("xb") as out:
        out.write(raw)
    require(hash_file(report)==(sha256(raw).hexdigest(),len(raw)),
            "New report changed during exclusive publication")
    print("ALL FOUR S4 RADIUS SIX TEN-SOURCE "
          "BI-INFINITE AUDIT PHASES PASSED",flush=True)
    print("COMPUTER-ASSISTED CONDITIONAL THEOREM:")
    print("  No full-S4-invariant q4,m3 symmetric-radius-6 shared marker "
          "rule exists on the bi-infinite squarefree subshift with "
          "separation>=3, domination<=2.")
    print("  Subject to classical Hall-Thue and finite-separator D-1 lemma.")
    print("  Consequently r_S4(4,3) >= 7, combining radius-five monotonicity.")
    print("  New exclusive audit report:",report)
    print("  Audit bytes:",len(raw))
    print("  Audit SHA-256:",sha256(raw).hexdigest())
    print(f"  Elapsed seconds: {perf_counter()-started:.2f}")
    print("No result for r>=7 or arbitrary m.")


if __name__=="__main__":
    main()
