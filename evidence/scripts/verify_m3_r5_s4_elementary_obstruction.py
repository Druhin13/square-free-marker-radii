#!/usr/bin/env python3
"""Verify a 23-letter obstruction to every 4-cycle-invariant m=3 r=5 rule.

The theorem: No shift-equivariant Boolean radius-5 rule on the bi-infinite
quaternary square-free subshift satisfies separation >=3 and domination
radius <=2 IF it is invariant under relabeling the four alphabet symbols.

Proof:
  W = 012032130120321 is a bi-infinitely extendible square-free factor.
  The five length-11 windows of W canonicalize to A,B,A,B,A. In fact the
  SAME 4-cycle g = (0->2,1->0,2->3,3->1) maps each i-window to (i+2)-window.
  Thus invariance under g alone forces the A,B,A,B,A contradiction.
  Conjugating g by arbitrary alphabet renamings shows the same holds for
  EVERY 4-cycle in S4. Full S4 invariance is a special case.

Bi-infinite extension certificate:
  Z = 12101203213012032101202 is square-free and contains W at offset 3.
  The occurrences of distinguished letter 3 in Z are at positions 7,10,15,
  giving span D=8 and 7-character, 3-free Hall-Thue exteriors on BOTH ends.
  The left exterior '1210120' and right exterior '2101202' occur as factors
  in the classical Hall-Thue fixed point of 0->012,1->02,2->1, at offsets
  21 and 22 of the fifth iterate phi^5(0).

By the finite separator extension lemma, the two exteriors can be
independently completed with infinite ternary square-free Hall-Thue tails:
any square involving 3 would have period <=D and be fully contained in Z;
all 3-free sections lie in square-free ternary tails. Thus W occurs in
a BI-INFINITE square-free quaternary word, not just a dead-end finite word.

This script checks all FINITE facts directly and derives the logical
contradiction by enumerating all four assignments to A,B. The classical
Hall-Thue theorem and the separator extension lemma are mathematical
inputs, not mechanically reproved here.

No external solver, SAT formula or DRAT verifier is required.
Run:
    python3 -m scripts.verify_m3_r5_s4_elementary_obstruction
"""
from itertools import permutations, product

W = "012032130120321"
Z = "12101203213012032101202"
MORPHISM = {"0": "012", "1": "02", "2": "1"}
SEPARATOR = "3"
EXPECTED_A = "01203213012"
EXPECTED_B = "01231032012"


def is_squarefree(word):
    """Check EVERY possible square at EVERY position; not just suffixes."""
    n = len(word)
    for start in range(n):
        for period in range(1, (n - start) // 2 + 1):
            left = word[start:start+period]
            right = word[start+period:start+2*period]
            if left == right:
                raise ValueError(
                    f"Square {left + right!r} at [{start}:{start+2*period}] "
                    f"inside {word!r}"
                )
    return True


def normalize_first_appearance(word):
    seen = {}
    result = []
    for c in word:
        if c not in seen:
            seen[c] = str(len(seen))
        result.append(seen[c])
    return "".join(result)


def main():
    print("S4-INVARIANT q=4,m=3,r=5 — ELEMENTARY OBSTRUCTION CHECK", flush=True)
    if len(W) != 15 or len(Z) != 23:
        raise ValueError("Unexpected witness lengths")
    if Z[3:18] != W:
        raise ValueError("Target W is not present at declared offset 3")
    is_squarefree(W)
    is_squarefree(Z)
    print("PHASE 1/4 PASSED: W length 15, Z length 23, both square-free")
    print("  15-letter W:", W)
    print("  23-letter Z:", Z)
    print("  Embedded W offset: 3")

    spots = [i for i, c in enumerate(Z) if c == SEPARATOR]
    if spots != [7, 10, 15]:
        raise ValueError(f"Unexpected separator locations: {spots}")
    D = spots[-1] - spots[0]
    left = Z[:spots[0]]
    right = Z[spots[-1]+1:]
    if D != 8 or len(left) != D-1 or len(right) != D-1:
        raise ValueError("Separator span/margins do not satisfy D-1")
    if "3" in left or "3" in right:
        raise ValueError("Exterior must omit the separator")

    hall = "0"
    for _ in range(5):
        hall = "".join(MORPHISM[c] for c in hall)
    is_squarefree(hall)
    if len(hall) != 48 or hall[21:28] != left or hall[22:29] != right:
        raise ValueError("Hall-Thue factor occurrence certificate fails")
    if left != "1210120" or right != "2101202":
        raise ValueError("Unexpected left/right ternary exterior")
    print("PHASE 2/4 PASSED: generalized separator extension certificate")
    print("  Separator 3 at:", spots, "span D:", D)
    print("  Left exterior:", left, "Hall-Thue phi^5 at offset 21")
    print("  Right exterior:", right, "Hall-Thue phi^5 at offset 22")
    print("  Margins >= D-1:", len(left), len(right))
    print("  Bi-infinite extension: Hall-Thue + finite-separator lemma")

    actual_windows = [W[i:i+11] for i in range(5)]
    actual_patterns = [normalize_first_appearance(window)
                       for window in actual_windows]
    if actual_patterns != [
        EXPECTED_A, EXPECTED_B, EXPECTED_A, EXPECTED_B, EXPECTED_A
    ]:
        raise ValueError(f"Sliding-block context pattern mismatch: "
                         f"{actual_patterns}")

    # Stronger audit: the SAME alphabet 4-cycle maps each window at
    # offset i onto the window at offset i+2 (for i = 0,1,2).
    # The contradiction thus needs only invariance under this one
    # 4-cycle, not invariance under all 24 elements of S4.
    cycle = (2, 0, 3, 1)

    def apply_perm(word, perm):
        return "".join(str(perm[int(letter)]) for letter in word)

    def inverse_perm(perm):
        inv = [None] * 4
        for source, target in enumerate(perm):
            inv[target] = source
        if set(inv) != set(range(4)):
            raise ValueError("Not a valid alphabet permutation")
        return tuple(inv)

    def compose(p, q):
        return tuple(p[q[i]] for i in range(4))

    identity = tuple(range(4))
    if compose(cycle, cycle) == identity or (
        compose(compose(cycle, cycle), cycle) == identity
    ) or compose(compose(compose(cycle, cycle), cycle), cycle) != identity:
        raise ValueError("Expected an alphabet permutation of order four")
    for i in range(3):
        if apply_perm(actual_windows[i], cycle) != actual_windows[i+2]:
            raise ValueError("4-cycle does not map i-window to i+2-window")

    conjugates = set()
    for perm in permutations(range(4)):
        inv = inverse_perm(perm)
        conjugate = compose(compose(perm, cycle), inv)
        conjugates.add(conjugate)
        renamed = apply_perm(W, perm)
        renamed_windows = [renamed[i:i+11] for i in range(5)]
        for i in range(3):
            if apply_perm(renamed_windows[i], conjugate) != renamed_windows[i+2]:
                raise ValueError("Relabeled word fails conjugate cycle pattern")
    if len(conjugates) != 6:
        raise ValueError(f"Expected six distinct alphabet four-cycles; got {len(conjugates)}")

    print("PHASE 3/4 ALSO PASSED: SAME 4-cycle relates every 2-step window")
    print("  g mapping 0,1,2,3 to:", cycle)
    print("  Order of g: 4")
    print("  All six conjugate 4-cycles independently checked: YES")

    # Invariance under the single cycle g already makes windows
    # at distance two share their Boolean marker decision.
    # Separation >=3 imposes NOT(A AND A) on positions 0,2 and
    # NOT(B AND B) on positions 1,3, simplifying to ~A and ~B.
    # Domination at central position requires A OR B.
    # Separation >=3 imposes NOT(A AND A) on positions 0,2 and
    # NOT(B AND B) on positions 1,3, simplifying to ~A and ~B.
    # Domination at central position requires A OR B.
    constraints = [(-1,), (-2,), (1, 2)]
    if any(
        all(any((assignment[abs(lit)-1] if lit > 0
                 else not assignment[abs(lit)-1])
                for lit in clause)
            for clause in constraints)
        for assignment in product((False, True), repeat=2)
    ):
        raise ValueError("The three proposed clauses are not UNSAT")

    print("PHASE 3/4 PASSED: five length-11 windows normalize to A,B,A,B,A")
    for i, (window, pattern) in enumerate(zip(actual_windows,
                                               actual_patterns)):
        print(f"  position {i}: {window} -> {pattern}")
    print("PHASE 4/4 PASSED: 3-clause two-variable core is UNSAT")
    print("  From distance-two packing at 0,2: NOT A")
    print("  From distance-two packing at 1,3: NOT B")
    print("  From five-position domination: A OR B")
    print("  Exhaustively tested all four Boolean assignments")
    print("ALL FOUR PHASES PASSED")
    print("ELEMENTARY MATHEMATICAL THEOREM:")
    print("  No symmetric-radius-5 shift-equivariant Boolean marker rule")
    print("  invariant under ANY single alphabet 4-cycle exists on ALL")
    print("  bi-infinite quaternary square-free words for m=3.")
    print("  Unrestricted exact minimum symmetric radius remains 5.")
    print("  This does NOT prove a lower bound for unrestricted radius 6,")
    print("  or for S4-invariant rules of other radii, nor any novelty.")


if __name__ == "__main__":
    main()
