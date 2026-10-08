from pathlib import Path
import tempfile
import unittest

from audit_source import audit


class SourceAuditTests(unittest.TestCase):
    def test_nested_datafiles_and_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'AM2R.project.gmx': r'''<assets>
                  <sprites><sprite>sprites\sTest</sprite></sprites>
                  <scripts><script>scripts\missing.gml</script></scripts>
                  <datafiles name="datafiles"><datafiles name="lang">
                    <datafile><filename>english.ini</filename></datafile>
                  </datafiles></datafiles></assets>''',
                'sprites/sTest.sprite.gmx': '<sprite><frames><frame>images/test.png</frame></frames></sprite>',
                'datafiles/lang/english.ini': '[Test]',
            }
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            report = audit(root)
            self.assertEqual(report['missing_counts'], {'sprite_image': 1, 'script': 1})
            self.assertFalse(report['assets_complete'])
            (root / 'sprites/images').mkdir()
            (root / 'sprites/images/test.png').write_bytes(b'fixture')
            (root / 'scripts').mkdir()
            (root / 'scripts/missing.gml').write_text('// fixture')
            self.assertTrue(audit(root)['assets_complete'])


if __name__ == '__main__':
    unittest.main()
