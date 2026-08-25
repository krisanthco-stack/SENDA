# Auditoría GitHub y visual — SENDA R6

**Release:** `SENDA-2026.08.25-R6-REVISION-FOLIO-GESTION`

## Fuente única

`index.html` es la única interfaz HTML oficial. GitHub Pages publica la raíz del repositorio después de ejecutar las pruebas.

## Reglas visuales verificadas

- Navegación: INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN.
- CONTROL conserva disposición y usa botones rápidos compactos; la opción activa cambia de color.
- CÉDULAS JURÍDICAS está disponible en CONTROL.
- INFORMACIÓN SENDA incorpora SELECCIONAR sin reacomodar las vistas existentes.
- Una selección activa oculta los demás FOLIOS / FINCAS hasta cancelar o finalizar.
- GESTIÓN incorpora REGRESAR A INFORMACIÓN SENDA y las exportaciones BASE GESTIÓN JSON / EXCEL.
- El icono oficial R6 se usa en encabezado y PWA.

## Barreras contra errores anteriores

- No existe HTML paralelo.
- No se usa EXP-2026 ni la etiqueta visual Expediente como identificador.
- No se fabrica Derecho `000`.
- Service Worker network-first y cache versionada R6.
- GitHub Actions debe aprobar pruebas antes de publicar.

## Resultado de auditoría visual R6

La interfaz se renderizó en Chromium a partir de la misma `index.html` oficial. El entorno de auditoría bloquea por política las URL `127.0.0.1` y `file://`, por lo que el documento se inyectó directamente en una página vacía de Chromium sin modificar su estructura ni lógica; únicamente se sustituyó `localStorage` por almacenamiento temporal de memoria para ejecutar la prueba.

Resultados:

- Escritorio 1440 px: INICIO, INFORMACIÓN SENDA, CONTROL y GESTIÓN sin desbordamiento horizontal.
- INFORMACIÓN SENDA: 19 botones SELECCIONAR visibles en la página inicial auditada.
- Revisión exclusiva: 1 único FOLIO / FINCA visible; panel y botón FINALIZAR presentes.
- FINALIZAR: folio ausente en INFORMACIÓN SENDA y presente en GESTIÓN.
- REGRESAR: folio nuevamente presente en INFORMACIÓN SENDA y ausente en GESTIÓN.
- CONTROL: CÉDULAS JURÍDICAS queda en estado activo por color.
- Móvil 390 px: ancho del documento 390 px; los 4 módulos permanecen accesibles y GESTIÓN queda dentro del viewport.
