# SENDA Control Gestión Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir el repositorio existente en una aplicación SENDA de carga trimestral, control de expedientes/movimientos y gestión auditada de registrados, preservando el motor registral actual.

**Architecture:** Mantener `src/registro.py` estable. Añadir módulos pequeños para reglas SENDA, persistencia SQLite y archivos ZIP/JSON/Excel. `app.py` orquesta tres módulos horizontales y usa las nuevas capas sin reemplazar la normalización existente.

**Tech Stack:** Python 3, Streamlit, pandas, SQLite (stdlib), XlsxWriter, openpyxl.

**Spec:** `docs/superpowers/specs/2026-08-23-senda-control-gestion-design.md`

## Global Constraints
- La funcionalidad registral existente debe permanecer disponible.
- Expediente visible = número de finca; `FINCA_ID` completo se conserva internamente.
- Orden predeterminado de movimientos = más antiguos a más recientes.
- Primera página = 25 registros; páginas posteriores = 20.
- Amarillo >60 y <90 días; rojo >=90 días.
- `REGISTRADO` exige operador y guarda fecha/hora/observación.
- JSON y Excel pertenecen al módulo GESTIÓN.

---

### Task 1: Reglas SENDA y expedientes
**Files:** Create `src/senda.py`; Test `tests/test_senda.py`.
**Produces:** `paginate_records`, `inactivity_level`, `movement_type`, `enrich_fincas`, `consolidate_movements`, `filter_records`.
- [ ] Escribir pruebas fallidas para paginación 25/20, alarmas, búsqueda por cédula/nombre/apellido y clasificación de movimientos.
- [ ] Ejecutar `pytest tests/test_senda.py -v` y confirmar fallos por funciones ausentes.
- [ ] Implementar las funciones mínimas.
- [ ] Ejecutar pruebas y confirmar PASS.

### Task 2: Persistencia y auditoría
**Files:** Create `src/database.py`; Test `tests/test_database.py`.
**Produces:** `init_db`, `save_dataset`, `save_movements`, `mark_registered`, `registered_ids`, `list_registered`, `audit_history`, `import_registered_records`.
- [ ] Escribir pruebas fallidas de registro, idempotencia y auditoría.
- [ ] Verificar RED.
- [ ] Implementar SQLite.
- [ ] Verificar GREEN.

### Task 3: ZIP trimestral e intercambio Gestión
**Files:** Create `src/io_tools.py`; Test `tests/test_io_tools.py`.
**Produces:** `expand_uploads`, `records_to_json_bytes`, `records_to_excel_bytes`, `read_management_import`.
- [ ] Escribir pruebas fallidas para ZIP, JSON y Excel.
- [ ] Verificar RED.
- [ ] Implementar.
- [ ] Verificar GREEN.

### Task 4: Regresión del motor existente
**Files:** Test `tests/test_registro_regression.py`; Modify `src/registro.py` sólo si una prueba demuestra necesidad.
- [ ] Probar lectura, normalización de `FINCA_ID`, operación histórica y planos sin finca.
- [ ] Ejecutar y confirmar PASS antes de integrar UI.

### Task 5: Interfaz Streamlit
**Files:** Modify `app.py`; Create `assets/app_icon.svg`; Modify `requirements.txt`.
**Consumes:** Tasks 1-4.
- [ ] Navegación horizontal y icono verde perlado.
- [ ] INFORMACIÓN SENDA con ZIP/trimestre, códigos agrupados, MS, descargas por código, búsqueda cédula/nombres/apellidos, acordeón y paginación.
- [ ] CONTROL con filtros, alarmas, expediente por finca, secciones hipotecas/gravámenes/segregaciones y registro auditado.
- [ ] GESTIÓN con registrados, filtros, quién/cuándo, historial e import/export JSON/Excel.
- [ ] Mantener las vistas registrales existentes dentro de INFORMACIÓN SENDA.

### Task 6: Verificación y entrega
**Files:** Modify `README.md`; create ZIP final.
- [ ] Ejecutar `pytest -q`.
- [ ] Ejecutar `python -m py_compile app.py src/*.py`.
- [ ] Ejecutar smoke test de procesamiento con los archivos suministrados.
- [ ] Actualizar README con instalación, módulos, base SQLite y flujo.
- [ ] Empaquetar repositorio actualizado.
