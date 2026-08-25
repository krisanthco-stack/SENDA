from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class WorkflowPythonBlocks(unittest.TestCase):
    def test_embedded_python_blocks_compile(self):
        text=(ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
        blocks=re.findall(r"python - <<'PY'\n((?:\s{10}.*\n)+?)\s{10}PY",text)
        self.assertGreaterEqual(len(blocks),2)
        for raw in blocks:
            code='\n'.join(line[10:] if line.startswith('          ') else line for line in raw.splitlines())
            compile(code,'<workflow>','exec')
if __name__=='__main__': unittest.main()
