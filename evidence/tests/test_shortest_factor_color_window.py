"""Audit the source-backed L=13 orbit-coloring obstruction."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
PROOF = ROOT / "proofs/m3/s4-L14-nine-color/square-free-marker-m3-r6-s4-orbit-preflight.json"
MORPHISM = {"0": "012", "1": "02", "2": "1"}

def squarefree(word):
    return not any(
        word[i:i+p] == word[i+p:i+2*p]
        for i in range(len(word))
        for p in range(1, (len(word)-i)//2+1)
    )

def hall(length=500):
    word = "0"
    while len(word) < length:
        word = "".join(MORPHISM[c] for c in word)
    return word

class ShortestColorWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(PROOF.read_text("utf-8"))[
            "sharp_label_length_13_counterexample"]

    def test_explicit_orbit_collision(self):
        w = self.record["target_length_15"]
        self.assertEqual(w, "021320310213203")
        self.assertTrue(squarefree(w))
        perm = self.record["four_cycle_image"]
        self.assertEqual(perm, [1,2,3,0])
        self.assertEqual(w[:13].translate(
            str.maketrans("0123", "".join(map(str,perm)))),
            w[2:15])
        self.assertEqual(w[:13], self.record["first_length_13_window"])
        self.assertEqual(w[2:15],
                         self.record["second_length_13_window_offset_2"])

    def test_full_biinfinite_source_extremities(self):
        r = self.record
        z = r["squarefree_extension_length_38"]
        self.assertEqual(len(z), 38)
        self.assertTrue(squarefree(z))
        self.assertEqual(z[12:27], r["target_length_15"])
        sep = [i for i,c in enumerate(z) if c == "0"]
        self.assertEqual(sep, [12,17,20,25])
        self.assertEqual((len(z[:sep[0]]),len(z[sep[-1]+1:])), (12,12))
        source = hall()
        for exterior, actual in [
            (r["left_exterior_hall"], z[:sep[0]]),
            (r["right_exterior_hall"], z[sep[-1]+1:]),
        ]:
            target = exterior["hall_factor"]
            offset = exterior["hall_prefix_offset"]
            self.assertEqual(source[offset:offset+len(target)], target)
            mapping = dict(exterior["original_hall_to_exterior_map"])
            self.assertEqual(target.translate(str.maketrans(mapping)), actual)
            self.assertEqual(exterior["original_exterior"], actual)

if __name__ == "__main__":
    unittest.main()
