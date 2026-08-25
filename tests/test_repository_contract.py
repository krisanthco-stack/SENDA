from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_only_one_root_html_interface_exists(self):
        html_files = sorted(p.name for p in ROOT.glob("*.html"))
        self.assertEqual(html_files, ["index.html"], "El repositorio debe tener una sola interfaz HTML oficial")

    def test_required_files_exist(self):
        for name in ("index.html", "manifest.webmanifest", "sw.js", "serve.py", "README.md", "DELIVERY_STANDARD.md"):
            self.assertTrue((ROOT / name).exists(), name)

    def test_manifest_identity(self):
        manifest_path = ROOT / "manifest.webmanifest"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn("SENDA", manifest["name"])
        self.assertEqual(manifest["start_url"], "./index.html")
        self.assertEqual(manifest["display"], "standalone")

    def test_pwa_references_single_source(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8") if (ROOT / "index.html").exists() else ""
        self.assertIn('rel="manifest" href="manifest.webmanifest"', index)
        self.assertIn("serviceWorker.register", index)
        self.assertIn("assets/app_icon_senda_r6.png", index)

    def test_release_identifier_is_consistent_and_not_duplicated(self):
        release = "SENDA-2026.08.25-R6-REVISION-FOLIO-GESTION"
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(index.count(release), 2, "index debe mostrar y declarar una sola versión lógica")
        self.assertEqual(readme.count(release), 1, "README debe declarar exactamente la misma versión")
        self.assertNotIn("GITHUB-AUDITADO-GITHUB-AUDITADO", readme)

    def test_readme_declares_single_source_and_release(self):
        p = ROOT / "README.md"
        self.assertTrue(p.exists())
        text = p.read_text(encoding="utf-8")
        self.assertIn("SENDA-2026.08.25-R6-REVISION-FOLIO-GESTION", text)
        self.assertIn("index.html", text)
        self.assertIn("única fuente de verdad", text.lower())

    def test_delivery_standard_contains_preservation_rule(self):
        p = ROOT / "DELIVERY_STANDARD.md"
        self.assertTrue(p.exists())
        text = p.read_text(encoding="utf-8").lower()
        self.assertIn("si está bien", text)
        self.assertIn("no se solicita eliminar", text)
        self.assertIn("se mantiene", text)


if __name__ == "__main__":
    unittest.main()

class GitHubPagesAuditTests(unittest.TestCase):
    def test_github_pages_workflow_deploys_the_repository_root(self):
        workflow = ROOT / ".github" / "workflows" / "pages.yml"
        self.assertTrue(workflow.exists(), "Debe existir despliegue explícito para GitHub Pages")
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("actions/upload-pages-artifact", text)
        self.assertRegex(text, r"(?m)^\s*path:\s*\.\s*$")
        self.assertIn("actions/deploy-pages", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("node --check", text)

    def test_github_validation_runs_functional_javascript_contract(self):
        script = ROOT / "tests" / "js_logic_test.js"
        self.assertTrue(script.exists(), "Debe existir prueba funcional JavaScript")
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("node tests/js_logic_test.js", workflow)

    def test_nojekyll_prevents_github_from_transforming_the_site(self):
        self.assertTrue((ROOT / ".nojekyll").exists(), ".nojekyll debe acompañar el sitio estático")

    def test_git_does_not_track_generated_runtime_files(self):
        import subprocess
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        forbidden = [p for p in tracked if "__pycache__" in p or p.endswith(".pyc") or (p.endswith((".db", ".sqlite", ".sqlite3")) and p != "data/registro_inmobiliario_base.sqlite")]
        self.assertEqual(forbidden, [], f"Archivos generados rastreados: {forbidden}")

    def test_static_base_sqlite_download_is_preserved(self):
        db = ROOT / "data" / "registro_inmobiliario_base.sqlite"
        self.assertTrue(db.exists(), "Debe preservarse la descarga de la base SQLite")
        self.assertGreater(db.stat().st_size, 1024)
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Descargar base SQLite", index)
        self.assertIn("data/registro_inmobiliario_base.sqlite", index)

    def test_service_worker_shell_files_exist_in_github_artifact(self):
        for rel in ("index.html", "manifest.webmanifest", "assets/app_icon_senda_r6.png", "data/registro_inmobiliario_base.sqlite"):
            self.assertTrue((ROOT / rel).exists(), f"Recurso PWA ausente: {rel}")
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotRegex(index, r'(?:href|src)="/(?!/)')

    def test_service_worker_is_forced_to_refresh_on_new_deploy(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        sw = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertIn("updateViaCache:'none'", index)
        self.assertIn("reg.update()", index)
        self.assertIn("controllerchange", index)
        self.assertIn("cache:'reload'", sw)
        self.assertRegex(sw, r"keys\.filter\(key\s*=>\s*key\.startsWith\('senda-'\)")
