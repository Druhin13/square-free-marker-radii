"""Small independent regression tests for ordered-color radius bounds.

These are combinatorial sanity checks, not a substitute for the
66,047-vertex original factor graph audit or a formal infinite-word proof.
"""
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from tools.verify_manifest import ROOT, verify_registry


def markers(colors, palette_size, circular=False):
    """Finite color-ranked parallel independent-set selection."""
    result = [False] * len(colors)
    for k in range(palette_size):
        # The recurrence may inspect only STRICTLY LOWER color rounds.
        # Never let an earlier site in the same round block another.
        lower_rounds = result[:]
        for i, color in enumerate(colors):
            if color != k:
                continue
            neighbors = (
                (i+d) % len(colors) if circular else i+d
                for d in (-2,-1,1,2)
            )
            if not any(
                lower_rounds[j]
                for j in neighbors
                if 0 <= j < len(colors)
            ):
                result[i] = True
    return result


class PublicationManifestTests(unittest.TestCase):
    def test_all_certified_original_proof_bytes(self):
        self.assertEqual(
            verify_registry(ROOT / "artifacts/manifest.json", full=True),
            (21, 51483416),
        )

    def test_registry_rejects_path_traversal(self):
        source = json.loads(
            (ROOT / "artifacts/manifest.json").read_text(encoding="utf-8")
        )
        source["artifacts"][0]["relative_path"] = "proofs/m3/../../hidden.txt"
        with tempfile.TemporaryDirectory() as root:
            edited = Path(root) / "bad-manifest.json"
            edited.write_text(json.dumps(source), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                verify_registry(edited, full=False)


class OrderedColorMarkerTests(unittest.TestCase):
    def test_cyclic_colorings_maintain_separation_and_domination(self):
        for palette_size in (3,4,5):
            length = palette_size * 4
            for order in itertools.permutations(range(palette_size)):
                colors = [order[i % palette_size] for i in range(length)]
                selected = markers(colors, palette_size, circular=True)
                self.assertTrue(any(selected))
                for i in range(length):
                    if selected[i]:
                        for d in (1,2):
                            self.assertFalse(selected[(i+d) % length])
                    else:
                        self.assertTrue(any(
                            selected[(i+d) % length]
                            for d in (-2,-1,1,2)
                        ))

    def test_color_rank_decision_uses_only_radius_two_times_C_minus_one(self):
        rng = random.Random(20261114)
        palette_size = 4
        radius = 2 * (palette_size-1)
        center = 20
        for _ in range(100):
            first = [rng.randrange(palette_size) for _ in range(41)]
            second = [rng.randrange(palette_size) for _ in range(41)]
            second[center-radius:center+radius+1] = first[
                center-radius:center+radius+1
            ]
            self.assertEqual(
                markers(first,palette_size)[center],
                markers(second,palette_size)[center],
            )

    def test_exact_nine_color_centered_window_radius(self):
        # Length-14 factor at [i-6, i+7], nine ranks -> eight hops of
        # radius two in each direction. The exact left/right dependency
        # radii are 22 and 23 respectively.
        L = 14
        C = 9
        left = (L-1)//2 + 2*(C-1)
        right = L//2 + 2*(C-1)
        self.assertEqual((left, right), (22, 23))
        self.assertEqual(max(left,right), 23)


    def test_nine_color_fourteen_symbol_window_locality(self):
        # The color at i uses source indices [i-6,i+7]; eight steps
        # of distance at most two give input offsets [-22,+23].
        # This does not replace the independent proper-coloring audit.
        rng = random.Random(20261114)
        center, length, palette_size = 60, 121, 9

        def arbitrary_local_colors(source):
            result = [0] * len(source)
            for i in range(7, len(source)-7):
                result[i] = sum(
                    (j + 1) * (value + 1)
                    for j, value in enumerate(source[i-6:i+8])
                ) % palette_size
            return result

        for _ in range(75):
            first = [rng.randrange(4) for _ in range(length)]
            second = [rng.randrange(4) for _ in range(length)]
            second[center-22:center+24] = first[center-22:center+24]
            self.assertEqual(
                markers(arbitrary_local_colors(first), palette_size)[center],
                markers(arbitrary_local_colors(second), palette_size)[center],
            )


if __name__ == "__main__":
    unittest.main()
