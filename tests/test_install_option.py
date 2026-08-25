from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class InstallOptionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.index=(ROOT/'index.html').read_text(encoding='utf-8')
    def test_visible_install_button_exists(self):
        self.assertIn('id="installSendaBtn"', self.index)
        self.assertIn('INSTALAR SENDA', self.index)
    def test_native_pwa_prompt_is_handled(self):
        self.assertIn('beforeinstallprompt', self.index)
        self.assertIn('appinstalled', self.index)
        self.assertIn('installSenda()', self.index)
    def test_ios_fallback_instructions_exist(self):
        self.assertIn('Añadir a pantalla de inicio', self.index)
if __name__=='__main__': unittest.main()
