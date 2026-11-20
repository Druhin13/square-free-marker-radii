"""Independent finite four-cycle witness regression."""
import unittest
from scripts import verify_m3_r5_s4_elementary_obstruction as original

def squarefree(word):
    return all(word[i:i+p]!=word[i+p:i+2*p]
               for i in range(len(word))
               for p in range(1,(len(word)-i)//2+1))

class FourCycleWitness(unittest.TestCase):
    def test_exact_source_word_and_extension(self):
        word,extended=original.W,original.Z
        self.assertEqual((len(word),len(extended)),(15,23))
        self.assertTrue(squarefree(word))
        self.assertTrue(squarefree(extended))
        self.assertEqual(extended[3:18],word)
        marked=[i for i,c in enumerate(extended) if c=='3']
        self.assertEqual(marked,[7,10,15])
        distance=marked[-1]-marked[0]
        self.assertEqual(distance,8)
        self.assertEqual(extended[:marked[0]],'1210120')
        self.assertEqual(extended[marked[-1]+1:],'2101202')
        self.assertEqual((marked[0],len(extended)-marked[-1]-1),(distance-1,)*2)

    def test_four_cycle_relates_opposite_contexts(self):
        windows=[original.W[i:i+11] for i in range(5)]
        perm=str.maketrans('0123','2031')
        self.assertEqual(windows[0],'01203213012')
        self.assertEqual(windows[1],'12032130120')
        self.assertEqual(windows[0],original.EXPECTED_A)
        for i in range(3):self.assertEqual(windows[i].translate(perm),windows[i+2])

if __name__=='__main__':unittest.main()
