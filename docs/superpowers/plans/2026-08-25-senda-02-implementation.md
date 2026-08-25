# SENDA 02 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir SENDA 02 como repositorio web/PWA independiente con la propuesta visual azul real y toda la lógica operativa aprobada.

**Architecture:** Un único `index.html` es la interfaz oficial y fuente de verdad visual. Los datos base y la lógica funcional se portan de R6 sin modificar R6; assets/PWA/Pages/pruebas viven en el repositorio SENDA 02.

**Tech Stack:** HTML5, CSS3, JavaScript ES2022, Web Storage, Service Worker/PWA, GitHub Pages, Python pytest para contratos, Node.js para auditorías JS.

**Spec:** `docs/superpowers/specs/2026-08-25-senda-02-design.md`

## Global Constraints
- No modificar SENDA R6.
- Navegación exacta: INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN.
- No mostrar "Expediente", `EXP-`, "Número de finca" ni `-000` como folio real.
- `index.html` de SENDA 02 es la única interfaz oficial.
- Mantener RAR/ZIP, PWA, selección exclusiva, FINALIZAR → GESTIÓN, REGRESAR, auditoría y JSON/Excel.

---

### Task 1: Contrato de aislamiento y UI
**Files:** Create `tests/test_senda02_contract.py`, `tests/test_senda02_runtime.py`.
- [ ] Escribir pruebas que fallen si falta `index.html`, si faltan los cuatro módulos, si reaparecen términos prohibidos, si falta el diseño azul, los KPI, CONTROL acordeón y los flujos aprobados.
- [ ] Ejecutar `pytest -q` y confirmar fallo por ausencia de implementación.

### Task 2: Aplicación SENDA 02
**Files:** Create `index.html`, `assets/app_icon_senda02.png`, `data/registro_inmobiliario_base.sqlite`.
- [ ] Implementar estructura visual azul sin alterar reglas funcionales.
- [ ] Portar lógica R6 de carga, filtros, folios, revisión, control, gestión y auditoría.
- [ ] Ejecutar pruebas y corregir hasta verde.

### Task 3: PWA y GitHub Pages
**Files:** Create `manifest.webmanifest`, `sw.js`, `.github/workflows/pages.yml`, `.nojekyll`, `serve.py`.
- [ ] Configurar caché exclusivo `senda02-*` y actualización segura.
- [ ] Publicar raíz del repositorio sólo si pruebas pasan.
- [ ] Probar rutas relativas.

### Task 4: Documentación y auditoría final
**Files:** Create `README.md`, `DELIVERY_STANDARD.md`, `AUDITORIA_SENDA02.md`.
- [ ] Documentar instalación, RAR/ZIP, flujo de revisión y reglas de preservación.
- [ ] Ejecutar suite completa, auditoría JS y verificación visual.
- [ ] Empaquetar ZIP desde archivos rastreados.
- [ ] Extraer ZIP a carpeta limpia y repetir suite completa.
