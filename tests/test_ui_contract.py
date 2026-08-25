from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


class UIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""

    def test_index_exists(self):
        self.assertTrue(INDEX.exists(), "index.html debe ser la única interfaz oficial")

    def test_main_navigation_order(self):
        nav = re.search(r"<nav>(.*?)</nav>", self.html, re.S | re.I)
        self.assertIsNotNone(nav)
        labels = re.findall(r">\s*(INICIO|INFORMACIÓN SENDA|CONTROL|GESTIÓN)\s*<", nav.group(1), re.I)
        self.assertEqual([x.upper() for x in labels], ["INICIO", "INFORMACIÓN SENDA", "CONTROL", "GESTIÓN"])

    def test_four_sections_exist(self):
        for section_id in ("inicio", "senda", "control", "gestion"):
            self.assertRegex(self.html, rf'<section[^>]+id="{section_id}"')

    def test_inicio_keeps_quarterly_load(self):
        for text in ("Cargar corte trimestral", "Año del corte", "Trimestre", "Procesar y guardar carga", "Inventario de la última carga"):
            self.assertIn(text, self.html)
        self.assertRegex(self.html, r'accept="[^"]*\.xls[^"]*\.txt[^"]*\.csv[^"]*\.json[^"]*\.zip')

    def test_folio_is_visible_identifier(self):
        self.assertIn("FOLIO / FINCA", self.html)
        self.assertIn("4-200103-001", self.html)
        self.assertNotRegex(self.html, r"(?i)EXP-2026-")
        self.assertNotRegex(self.html, r"(?i)>\s*Expediente(?:s)?\s*<")
        self.assertNotRegex(self.html, r"(?i)>\s*Número de finca\s*<")

    def test_information_senda_filters_and_original_views(self):
        for text in ("Mes del movimiento", "Cédula", "Plano", "Nombre / apellidos"):
            self.assertIn(text, self.html)
        for view in ("Fincas/Folios", "Movimientos", "Segregaciones", "Planos", "Gravámenes", "Históricos", "Anotaciones", "Jurídicas", "Códigos"):
            self.assertIn(view, self.html, f"Vista registral original ausente: {view}")

    def test_alarms_and_codes_share_same_row(self):
        start = self.html.find('<div class="dual">')
        end = self.html.find('<div class="panel"><div class="section-head">', start)
        self.assertGreaterEqual(start, 0)
        self.assertGreater(end, start)
        dual = self.html[start:end]
        self.assertIn("ALARMAS", dual)
        self.assertIn("CÓDIGOS", dual)
        self.assertIn("Más de 2 meses", dual)
        self.assertIn("3 meses o más", dual)
        self.assertIn("MS · Mostrar seleccionado", dual)

    def test_control_preserves_actions_and_quick_filters(self):
        for text in ("Hipotecas", "Gravámenes", "Segregaciones", "Anotaciones", "GUARDAR FOLIO", "ELIMINAR FOLIO", "FINALIZADO"):
            self.assertIn(text, self.html)
        for fn in ("saveFolio", "deleteFolio", "finishFolio"):
            self.assertRegex(self.html, rf"function\s+{fn}\s*\(")
        self.assertIn("Historial general de acciones por folio", self.html)

    def test_gestion_preserves_filters_audit_and_import_export(self):
        for text in ("Importar / Exportar Gestión", "Mes del movimiento", "Mes finalizado / registrado", "Finalizado por", "Exportar JSON", "Exportar Excel"):
            self.assertIn(text, self.html)
        for field in ("finalizado_por", "finalizado_en", "observacion"):
            self.assertIn(field, self.html)

    def test_pagination_contract(self):
        self.assertIn("function pageCount(n){return n<=25?1:1+Math.ceil((n-25)/20)}", self.html)
        self.assertIn("size=p===1?25:20", self.html)

    def test_format_folio_requires_province_number_and_right(self):
        m = re.search(r"function\s+formatFolio\s*\([^)]*\)\{([^}]+)\}", self.html)
        self.assertIsNotNone(m)
        self.assertRegex(m.group(1), r"!p\s*\|\|\s*!n\s*\|\|\s*!d", "No debe formar folio sin Derecho")

    def test_local_storage_persistence(self):
        self.assertIn("localStorage", self.html)


if __name__ == "__main__":
    unittest.main()

class DeepVisualRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")

    def test_seed_data_never_exposes_placeholder_right_000(self):
        self.assertNotRegex(self.html, r'"folio":"\d+-\d+-000"')

    def test_uploaded_or_stored_folios_reject_placeholder_right_000(self):
        self.assertRegex(self.html, r"function\s+normalizeFolioValue\s*\(")
        self.assertIn("if(d==='000')return ''", self.html)
        self.assertIn("normalizeFolioValue(r.FOLIO_REAL)", self.html)
        self.assertIn("normalizeFolioValue(r.folio)", self.html)

    def test_original_movements_preserves_category_filter_and_csv_download(self):
        self.assertIn("Categoría", self.html)
        self.assertIn("Descargar movimientos CSV", self.html)
        self.assertRegex(self.html, r"function\s+downloadOriginalMovementsCsv\s*\(")

    def test_planos_preserves_unlocated_metric(self):
        self.assertIn("Planos sin finca localizada", self.html)

    def test_gestion_import_accepts_json_and_excel(self):
        self.assertRegex(self.html, r'id="gImport"[^>]+accept="[^"]*\.json[^"]*\.xls[^"]*\.xlsx')
        self.assertIn("Importar registrados JSON / Excel", self.html)
        self.assertRegex(self.html, r"function\s+parseGestionExcel\s*\(")

    def test_mobile_navigation_keeps_all_four_modules_visible_without_horizontal_scroll(self):
        self.assertIn("nav{flex-wrap:wrap;overflow:visible}", self.html)
        self.assertIn("nav button{flex:1 1 calc(50% - 4px)", self.html)
