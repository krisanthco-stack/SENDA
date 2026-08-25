# Auditoría SENDA 02

## Separación
SENDA 02 se creó en un repositorio independiente. Durante esta construcción SENDA R6 se usó sólo como referencia de lógica/datos; la nueva interfaz, almacenamiento, Service Worker, manifiesto y GitHub Pages pertenecen a SENDA 02.

## Identidad técnica
- Release: `SENDA-02-2026.08.25-R1`
- Datos locales: `senda02_data`
- Estado operativo: `senda02_state`
- Catálogo: `senda02_catalog`
- Caché PWA: prefijo `senda02-`

## Auditoría visual ejecutada
Playwright cargó el `index.html` real en una página aislada con el mismo JavaScript y comprobó:
- Escritorio 1440×1000: `scrollWidth = innerWidth = 1440`.
- Móvil 390×844: `scrollWidth = innerWidth = 390`.
- Los cuatro botones INICIO / INFORMACIÓN SENDA / CONTROL / GESTIÓN permanecen visibles.
- La cabecera azul, panel lateral, cinco KPI, bloque de trimestre y espacio de trabajo corresponden a la propuesta visual aplicada.

## Flujo verificado
- INFORMACIÓN SENDA: selección de `4-281453-001` → 1 FOLIO / FINCA visible en toda la vista registral y resultados.
- FINALIZAR REVISIÓN → el folio deja de aparecer en pendientes y entra a GESTIÓN.
- REGRESAR A INFORMACIÓN SENDA → sale de GESTIÓN y vuelve a pendientes.
- CONTROL: 150 folios iniciales → 1 acordeón visible tras seleccionar; tarjeta resaltada por color.
- CÉDULAS JURÍDICAS: botón adquiere clase `active`.
- Móvil: sin desbordamiento horizontal.

## Archivos de evidencia
- `audit_visual/desktop_inicio.png`
- `audit_visual/desktop_senda_revision.png`
- `audit_visual/desktop_control_selected.png`
- `audit_visual/desktop_gestion_finalizado.png`
- `audit_visual/mobile_inicio.png`

## Terminología prohibida
La auditoría comprueba que `index.html` no contiene `EXP-2026`, `Número de finca`, etiquetas visibles `Expediente` ni FOLIO / FINCA artificial `-000`.

## SENDA 02 R2 · CONTROL

Se añadió selección centralizada en CONTROL, DESELECCIONAR sin finalizar y FINALIZAR con traslado a GESTIÓN. La caché PWA se incrementó a `senda02-2026-08-25-r2-control`.
