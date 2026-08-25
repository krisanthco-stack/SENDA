# SENDA 02

Repositorio independiente de SENDA R6. **No sustituye ni modifica R6.**

La interfaz oficial es `index.html` y utiliza la propuesta visual azul aprobada con cuatro módulos: **INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN**.

## Funciones
- Carga individual, ZIP y RAR en INICIO.
- PWA instalable con botón `INSTALAR SENDA`.
- Identificación única `FOLIO / FINCA` (`Provincia-Número-Derecho`).
- Selección exclusiva en INFORMACIÓN SENDA.
- CONTROL con acordeones, selección por color, ocultamiento de los demás folios y CÉDULAS JURÍDICAS.
- FINALIZAR REVISIÓN → GESTIÓN y REGRESAR A INFORMACIÓN SENDA.
- Auditoría por usuario/fecha/observación.
- Base GESTIÓN JSON y Excel con tipos de gestión.
- GitHub Pages publica este mismo `index.html` después de ejecutar pruebas.

## Ejecutar local
`python serve.py`

## GitHub Pages
Configure Pages con **GitHub Actions**. El workflow `.github/workflows/pages.yml` publica la raíz sólo si las pruebas pasan.

## R2 · Revisión centralizada en CONTROL

- La selección desde INFORMACIÓN SENDA abre el FOLIO / FINCA en CONTROL.
- CONTROL oculta los demás folios y abre el seleccionado en acordeón.
- Acciones: GUARDAR FOLIO · DESELECCIONAR · ELIMINAR FOLIO · FINALIZAR.
- DESELECCIONAR no cambia el estado del trámite ni lo mueve a GESTIÓN.
- FINALIZAR retira el folio de INFORMACIÓN SENDA y CONTROL y lo incorpora a GESTIÓN con auditoría.
