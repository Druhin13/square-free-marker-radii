"""Distribution-level release contract for the public evidence repository."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence'

class RepositoryMetadata(unittest.TestCase):
    def test_only_public_workflow_is_shipped(self):
        workflows=list(ROOT.rglob('*.yml'))
        self.assertEqual(workflows,[ROOT/'.github/workflows/verify-evidence.yml'])
        self.assertFalse((EV/'paper').exists())
        self.assertFalse((EV/'.github').exists())

    def test_citation_licenses_and_reproduction_guide(self):
        for path in ('README.md','REPRODUCING.md','PROVENANCE.md',
                     'CITATION.cff','LICENSE.md','LICENSE-MIT.txt',
                     'LICENSE-CC-BY-4.0.md','SHA256SUMS'):
            self.assertTrue((ROOT/path).is_file(),path)
        self.assertIn('Druhin', (ROOT/'CITATION.cff').read_text('utf-8'))
        self.assertIn('CC BY 4.0', (ROOT/'LICENSE.md').read_text('utf-8'))
        self.assertIn('MIT', (ROOT/'LICENSE.md').read_text('utf-8'))

    def test_registry_keys_are_distribution_only(self):
        allowed={
            'manifest.json':{'schema_version','title','subject',
                'description','sha256_definition','artifact_count','artifacts'},
            'subgroup-manifest.json':{'schema_version','title','description',
                'scope','archive_count','archives'},
            'subgroup-positive-manifest.json':{'schema_version','title',
                'description','archive_count','archives'},
            'exact-symmetry-addendum-manifest.json':{'schema_version',
                'cases','files'},
        }
        for filename,keys in allowed.items():
            registry=json.loads((EV/'artifacts'/filename).read_text('utf-8'))
            self.assertEqual(set(registry),keys,filename)
        main=json.loads((EV/'artifacts/manifest.json').read_text('utf-8'))
        self.assertTrue(all(row['integrity_status']=='verified'
                            for row in main['artifacts']))

if __name__=='__main__':unittest.main()
