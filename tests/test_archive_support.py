from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ArchiveSupportContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / 'index.html').read_text(encoding='utf-8')

    def test_inicio_accepts_rar_and_zip_without_moving_module(self):
        m = re.search(r'<input id="iFiles"[^>]+accept="([^"]+)"', self.index)
        self.assertIsNotNone(m, 'Debe conservarse el selector de archivos de INICIO')
        accept = m.group(1).lower()
        self.assertIn('.zip', accept)
        self.assertIn('.rar', accept)

    def test_rar_runtime_is_explicit_and_version_pinned(self):
        self.assertIn('7z-wasm@1.2.0', self.index)
        self.assertIn('extractArchiveEntries', self.index)
        self.assertRegex(self.index, r"endsWith\('\.rar'\)")

    def test_zip_keeps_local_fast_path_and_rar_uses_wasm_fallback(self):
        self.assertIn('async function unzipEntries', self.index)
        self.assertIn('async function extractArchiveEntries', self.index)
        self.assertIn("ext==='zip'", self.index)
        self.assertIn("ext==='rar'", self.index)

    def test_user_gets_clear_archive_error_not_silent_failure(self):
        self.assertIn('No se pudo descomprimir', self.index)
        self.assertIn('RAR', self.index)
        self.assertIn('ZIP', self.index)

if __name__ == '__main__':
    unittest.main()
