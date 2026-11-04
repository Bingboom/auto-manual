from pathlib import Path
import sys,json,unittest,importlib.util,shutil
P=Path(__file__).resolve().parents[1];W=next(x for x in P.parents if (x/'build.py').is_file());sys.path[:0]=[str(W),str(P)]
spec=importlib.util.spec_from_file_location('source_target',W/'tests/test_jhp1000b_us_web.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.PACKAGE=P
# The original test expressly asserted that the back address was absent. Its
# new source-bound replacement verifies the operator's actual exclusions.
class CurrentSourceScope(unittest.TestCase):
 def test_cover_toc_excluded_and_back_contact_restored(self):
  s=(P/'web/en/manual_jhp1000b_us_en.md').read_text();self.assertNotIn('TABLE OF CONTENTS',s);self.assertNotIn('data-source-cover',s)
  for x in ['5310 Bunche Dr., Fremont, CA 94538-8301','hello@jackery.com','www.jackery.com','1-888-502-2236','data-source-preface-title','data-source-contact="back"']:self.assertIn(x,s)
  c=json.loads((P/'source/en/content.json').read_text());self.assertEqual(len(c['chapters']),17);self.assertEqual(c['chapters'][-1]['id'],'back-cover')
 def test_fcc_source_paragraph_break_and_wrapping(self):
  s=(P/"web/en/manual_jhp1000b_us_en.md").read_text();self.assertIn("Rules.\nThese limits",s);self.assertIn("white-space:pre-line",s);self.assertIn("float:left",s);self.assertEqual(len(m.BeautifulSoup(s,"html.parser").select(".hb-fcc-composition")),1)
 def test_transcription_bytes_unchanged(self):
  old=P.parent/'git-20261103-e546301b-source-alignment/source/transcription.json';self.assertEqual(old.read_bytes(),(P/'source/transcription.json').read_bytes())
 def test_source_rectangles_and_native_table_fixes(self):
  s=(P/'web/en/manual_jhp1000b_us_en.md').read_text();self.assertEqual(len(m.BeautifulSoup(s,'html.parser').select('[data-native-panel]')),7);self.assertEqual(len(m.BeautifulSoup(s,'html.parser').select('[data-native-strip]')),2);self.assertIn('V<sub>oc</sub>',s);self.assertIn('rowspan="2"',s)
alltests=unittest.defaultTestLoader.loadTestsFromModule(m);suite=unittest.TestSuite(t for g in alltests for t in g if t._testMethodName!='test_chapters_and_print_only_pages_excluded');suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CurrentSourceScope));r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
