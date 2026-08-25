from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ArchiveRuntimeCacheContract(unittest.TestCase):
    def test_service_worker_caches_rar_runtime_after_first_use(self):
        sw=(ROOT/'sw.js').read_text(encoding='utf-8')
        self.assertIn('7z-wasm@1.2.0/7zz.umd.js', sw)
        self.assertIn('7z-wasm@1.2.0/7zz.wasm', sw)
        self.assertIn('ARCHIVE_RUNTIME', sw)
        self.assertIn('cache.put', sw)
if __name__=='__main__': unittest.main()
