# Registro Inmobiliario · SENDA

## Entrega sincronizada R3 — 24/08/2026

Esta carpeta es una única versión activa: **SENDA-2026.08.24-R3**. `app.py` y `SENDA_VISTA_SINCRONIZADA.html` deben mostrar el mismo identificador de versión y utilizan el mismo icono definitivo `assets/app_icon_propuesta2.png`.

Reglas visibles de esta versión:

- El identificador mostrado es **FOLIO / FINCA**, conformado como `Provincia-Número de finca-Derecho`, por ejemplo `4-200103-001`.
- No se muestra numeración artificial de trámite.
- INFORMACIÓN SENDA incluye **Mes del movimiento** y una misma fila con los acordeones **🚨 ALARMAS** y **🏷️ CÓDIGOS**.
- CONTROL muestra la alerta 🟡/🔴 dentro del FOLIO / FINCA y las acciones **GUARDAR FOLIO**, **ELIMINAR FOLIO** y **FINALIZADO**.
- GESTIÓN conserva FOLIO / FINCA, tipo de derecho, plano y auditoría de finalización.
- El HTML se incluye como comprobación visual sincronizada; la aplicación funcional continúa siendo `app.py`.


Aplicación Streamlit para cargar cortes registrales, construir una base SQLite organizada y controlar movimientos por **folio real registral** con auditoría.

## Identificación registral

La interfaz no inventa números de trámite ni expediente. El folio real se conforma únicamente con los datos de la fuente:

`PROVINCIA - NÚMERO DE FINCA - DERECHO (3 dígitos)`

Ejemplos:

- `4-200103-001`
- `4-200103-002`
- `4-254163-000` cuando el Derecho real de la fuente es `0`.

Cantón y distrito **no** forman parte del folio real visible. `FINCA_ID`, `MOVIMIENTO_ID` y `EXPEDIENTE_ID` se conservan sólo como campos técnicos internos para trazabilidad y compatibilidad.

Si la fuente no aporta Derecho suficiente para construir el folio real, SENDA mantiene el movimiento sin folio identificable y lo informa; **no inventa `000` ni otro Derecho**.

## Derechos

Cada derecho de una misma finca se trata de forma independiente. El sistema interpreta `COD_DERECHO`:

- `D`: DOMINIO
- `H`: HABITACIÓN
- `N`: NUDA PROPIEDAD
- `U`: USUFRUCTO
- `S`: USO
- `C`: USUFRUCTO CONJUNTO

Por ejemplo, `4-108604-001` puede ser NUDA PROPIEDAD y `4-108604-009` USUFRUCTO; sus titulares, movimientos, planos, estado y acciones no se mezclan.

## INICIO

- Conserva el módulo de carga trimestral existente.
- Carga `.xls` tabulados, `.txt` y ZIP trimestrales.
- Asocia cada carga a Año + Trimestre.
- Construye/actualiza `data/registro_inmobiliario.db`.
- Muestra el inventario de la última carga.
- No usa numeración artificial de expediente; la identificación visible posterior es **FOLIO / FINCA**.

## INFORMACIÓN SENDA

- Búsqueda por cédula, nombre, apellidos, **FOLIO / FINCA**, plano y mes.
- Códigos agrupados con Mostrar / Ocultar / MS (Mostrar Seleccionado).
- Descarga por código en JSON o Excel.
- Primera página de 25 registros; páginas posteriores de 20.
- Alarmas: amarillo >60 y <90 días; rojo >=90 días.
- Descarga SQLite y exportación completa a Excel.

## CONTROL

CONTROL trabaja por **folio real exacto**, no por toda la finca.

Al abrir un folio muestra:

- Folio real (`4-200103-001`).
- Tipo de derecho.
- Plano(s).
- Titular(es) y cédula(s).
- Hipotecas, Gravámenes, Segregaciones, Anotaciones, Cierres, Rectificaciones y otros movimientos.

Acciones disponibles para el folio seleccionado:

- **GUARDAR FOLIO**: guarda una referencia operativa del folio y registra operador, fecha/hora y observación.
- **ELIMINAR FOLIO**: elimina únicamente ese folio de CONTROL/GESTIÓN, con confirmación explícita. Los archivos y tablas fuente permanecen intactos.
- **FINALIZADO**: transfiere a GESTIÓN sólo los movimientos pendientes de ese folio real. No arrastra otros Derechos de la misma finca.

El historial de auditoría permite ver quién guardó, finalizó o eliminó y cuándo ocurrió.

Los botones rápidos Hipotecas, Gravámenes, Segregaciones, Anotaciones, Aplicar y Limpiar mantienen el mismo estilo visual.

## GESTIÓN

- Muestra exclusivamente folios/movimientos finalizados.
- Conserva `FOLIO_REAL`, `TIPO_DERECHO`, finca, Derecho y plano.
- Visualiza quién finalizó/registró, fecha/hora y observación.
- Filtros por cédula, nombre, apellidos, **FOLIO / FINCA**, código, mes del movimiento, fecha y mes de finalización.
- Importación/exportación JSON y Excel dentro del mismo módulo.
- Importación idempotente por `MOVIMIENTO_ID` técnico interno.

## Persistencia SQLite

Tablas fuente/analíticas principales:

- `resumen`
- `fincas_folios`
- `historicos`
- `gravamenes`
- `segregaciones`
- `anotaciones`
- `planos_control`
- `alertas`
- `top_operaciones`
- `catalogo_operaciones`
- `manual_codigos`

Tablas operativas:

- `movimientos`
- `folios_guardados`
- `gestion_registrados`
- `auditoria`

Las bases creadas por versiones anteriores se migran al abrirse: cuando existen Provincia, Número de finca y Derecho suficientes, se completa `FOLIO_REAL` y `TIPO_DERECHO` sin recargar los cortes.

## Instalación

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pruebas

```bash
PYTHONPATH=. pytest -q
python -m py_compile app.py src/*.py
```

La verificación de integración carga el corte de Sarapiquí del 01-06-2026 y valida 8.837 movimientos consolidados, conformación de folios reales, separación de Derechos, Guardar, Finalizar, Eliminar y preservación de folios hermanos.

## Archivos principales

- `app.py`: interfaz Streamlit.
- `src/registro.py`: motor registral original preservado.
- `src/senda.py`: folios reales, derechos, filtros, paginación y alarmas.
- `src/database.py`: SQLite, Guardar/Eliminar/Finalizar y auditoría.
- `src/io_tools.py`: ZIP, JSON y Excel.
- `assets/app_icon_propuesta2.png`: icono definitivo.
- `tests/`: pruebas automatizadas.

## Nota

La clasificación automática es una herramienta de control y apoyo analítico. No sustituye certificaciones registrales, estudio de título ni revisión jurídica del asiento original.

## Corrección de interfaz FOLIO / FINCA

La identificación visible del registro se presenta como un único **FOLIO / FINCA**, por ejemplo `4-200103-001`. La interfaz no muestra un número de expediente inventado ni divide el identificador en campos visuales separados de finca y derecho. El **tipo de derecho** (Dominio, Usufructo, Nuda Propiedad, etc.) y el **plano** se conservan como datos descriptivos del folio.

## Regla de preservación funcional

- Si un módulo, botón, filtro o flujo existente funciona y no se solicita eliminarlo, se conserva.
- Las mejoras visuales no reordenan módulos ni cambian la lógica.
- INICIO conserva la carga trimestral; INFORMACIÓN SENDA, CONTROL y GESTIÓN conservan sus funciones.
- La identificación visible usa **FOLIO / FINCA**, por ejemplo `4-200103-001`; no se muestra numeración artificial de expediente.
- `app.py`, el HTML y el icono deben pertenecer al mismo `RELEASE_ID`.
