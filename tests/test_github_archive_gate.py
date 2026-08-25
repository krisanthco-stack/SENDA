from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GitHubArchiveGate(unittest.TestCase):
    def test_pages_workflow_runs_archive_runtime_test(self):
        text=(ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.assertIn('node tests/archive_runtime_test.js', text)
if __name__=='__main__': unittest.main()
