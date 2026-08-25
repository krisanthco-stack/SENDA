from pathlib import Path
import re, unittest
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
class R6ReviewContract(unittest.TestCase):
    def test_new_icon_is_single_official_asset(self):
        icons=list((ROOT/'assets').glob('*.png'))
        self.assertEqual([p.name for p in icons], ['app_icon_senda_r6.png'])
        self.assertIn('assets/app_icon_senda_r6.png', HTML)
        self.assertNotIn('app_icon_propuesta2.png', HTML)
    def test_information_senda_selects_exclusive_folio(self):
        self.assertIn('SELECCIONAR', HTML)
        self.assertIn('function selectReviewFolio', HTML)
        self.assertIn('function selectedReviewFolio', HTML)
        self.assertIn('Los demás folios permanecen ocultos', HTML)
        self.assertIn('FINALIZAR REVISIÓN DEL FOLIO / FINCA', HTML)
    def test_finish_moves_to_gestion_and_return_exists(self):
        self.assertIn("toast('FOLIO / FINCA salió de INFORMACIÓN SENDA y pasó a GESTIÓN')", HTML)
        self.assertIn('REGRESAR A INFORMACIÓN SENDA', HTML)
        self.assertIn('function returnFolioToSenda', HTML)
    def test_gestion_base_exports_json_excel_and_type(self):
        self.assertIn('BASE GESTIÓN JSON', HTML)
        self.assertIn('BASE GESTIÓN EXCEL', HTML)
        self.assertIn('tipo_gestion', HTML)
        for k in ['HIPOTECA','GRAVAMEN','SEGREGACION','ANOTACION']:
            self.assertIn(k, HTML)
    def test_control_compact_juridical_and_active_color(self):
        self.assertIn('CÉDULAS JURÍDICAS', HTML)
        self.assertRegex(HTML, r'\.control-quick\{[^}]*font-size:10px')
        self.assertRegex(HTML, r'\.control-quick\.active\{[^}]*background:var\(--dark\)')
        for k in ['HIPOTECA','GRAVAMEN','SEGREGACION','ANOTACION','JURIDICA']:
            self.assertIn(f'data-control-quick="{k}"', HTML)
    def test_no_legacy_visible_identifier(self):
        self.assertNotRegex(HTML, r'EXP-2026-')
        self.assertNotRegex(HTML, r'>\s*Número de finca\s*<')
if __name__=='__main__': unittest.main()
