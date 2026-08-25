# SENDA R5 Clean Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un repositorio web estático, instalable y funcional donde `index.html` sea la única interfaz SENDA y preserve todas las funciones no eliminadas explícitamente.

**Architecture:** Una aplicación HTML/CSS/JavaScript sin backend, basada en el HTML funcional R4 y con datos base embebidos. El estado operativo se almacena en `localStorage`; PWA usa `manifest.webmanifest` + `sw.js`. Pruebas Python inspeccionan el contrato estructural y JavaScript se valida con Node.

**Tech Stack:** HTML5, CSS3, JavaScript ES2022, Web Storage API, Service Worker, Web App Manifest, Python 3 unittest/pytest-compatible tests, Node.js syntax check.

**Spec:** `docs/superpowers/specs/2026-08-24-senda-r5-clean-repository-design.md`

## Global Constraints
- Mantener el formato visual establecido; no reacomodar módulos o controles existentes.
- Navegación principal exacta: INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN.
- No mostrar “Expediente”, `EXP-2026-` ni “Número de finca”.
- FOLIO / FINCA visible en formato provincia-número-derecho.
- Conservar toda función existente no solicitada explícitamente para eliminación.
- `index.html` es la única fuente de verdad visual.

---

### Task 1: Contrato de preservación y regresión

**Files:**
- Create: `tests/test_ui_contract.py`
- Create: `tests/test_repository_contract.py`

**Interfaces:**
- Consumes: `index.html`, `manifest.webmanifest`, `sw.js`.
- Produces: una suite que bloquea regresiones de módulos, etiquetas, vistas y acciones.

- [ ] **Step 1: Write the failing tests** que exigen cuatro módulos, carga de INICIO, FOLIO / FINCA, vistas originales, acciones por folio, mes, Alarmas+Códigos y ausencia de términos prohibidos.
- [ ] **Step 2: Run tests to verify they fail** con `python -m unittest discover -s tests -v` porque `index.html` aún no existe.
- [ ] **Step 3: Create the minimal repository files** en las tareas siguientes.
- [ ] **Step 4: Re-run tests** hasta obtener PASS.
- [ ] **Step 5: Commit** `test: define SENDA R5 preservation contract`.

### Task 2: Aplicación única index.html

**Files:**
- Create: `index.html`
- Create: `assets/app_icon_propuesta2.png`

**Interfaces:**
- Consumes: HTML funcional R4 como base aprobada y asset de icono R3.
- Produces: aplicación oficial única con cuatro módulos y persistencia local.

- [ ] **Step 1: Copy the approved R4 HTML into `index.html`** sin cambiar el orden de módulos.
- [ ] **Step 2: Replace embedded icon with `assets/app_icon_propuesta2.png`** manteniendo el mismo tamaño y cabecera.
- [ ] **Step 3: Restore original registral views** dentro de INFORMACIÓN SENDA sin mover los controles existentes.
- [ ] **Step 4: Restore general audit history** dentro de CONTROL sin mover la ficha de folio.
- [ ] **Step 5: Verify FOLIO / FINCA formatting and missing-right behavior**; nunca producir `-000` de forma inventada.
- [ ] **Step 6: Run UI contract tests** y corregir sólo las diferencias que violen el spec.
- [ ] **Step 7: Commit** `feat: build single-source SENDA R5 app`.

### Task 3: Instalación PWA y ejecución local

**Files:**
- Create: `manifest.webmanifest`
- Create: `sw.js`
- Create: `serve.py`

**Interfaces:**
- Consumes: `index.html`, icono.
- Produces: instalación PWA, caché offline y servidor local sin dependencias.

- [ ] **Step 1: Extend repository tests** para exigir manifest, service worker y referencias correctas.
- [ ] **Step 2: Verify tests fail** antes de crear esos archivos.
- [ ] **Step 3: Implement manifest and service worker** cacheando `./`, `./index.html`, el manifest y el icono.
- [ ] **Step 4: Implement `serve.py`** usando `http.server` en puerto configurable por argumento, predeterminado 8000.
- [ ] **Step 5: Re-run tests**.
- [ ] **Step 6: Commit** `feat: make SENDA R5 installable and offline-ready`.

### Task 4: Documentación y entrega reproducible

**Files:**
- Create: `README.md`
- Create: `DELIVERY_STANDARD.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: aplicación final.
- Produces: instrucciones GitHub Pages/local y regla de preservación visible en el repositorio.

- [ ] **Step 1: Add documentation contract checks** para versión y fuente única.
- [ ] **Step 2: Write README** con ejecución local, publicación en GitHub Pages, instalación PWA y límites del almacenamiento local.
- [ ] **Step 3: Write DELIVERY_STANDARD** con la regla “si está bien y no se solicita eliminar, se mantiene”.
- [ ] **Step 4: Run full tests and JavaScript syntax validation**.
- [ ] **Step 5: Commit** `docs: document SENDA R5 delivery standard`.

### Task 5: Auditoría del artefacto entregable

**Files:**
- Create: `RELEASE_VERIFICATION.txt`
- Package: `SENDA_REGISTRO_INMOBILIARIO_R5.zip`

**Interfaces:**
- Consumes: repositorio completo.
- Produces: ZIP Git-ready verificado desde una extracción limpia.

- [ ] **Step 1: Run full tests** con `python -m unittest discover -s tests -v`.
- [ ] **Step 2: Validate JavaScript syntax** extrayendo los scripts inline y ejecutando `node --check`.
- [ ] **Step 3: Scan forbidden visible labels** y archivos temporales.
- [ ] **Step 4: Create ZIP excluding `.git`, caches and temporary files**.
- [ ] **Step 5: Extract ZIP to a clean directory and repeat all tests**.
- [ ] **Step 6: Record exact verification results in `RELEASE_VERIFICATION.txt`** y reempaquetar si cambió.
