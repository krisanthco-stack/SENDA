# SENDA 02 — Diseño aprobado

## Objetivo
Crear una aplicación nueva e independiente llamada **SENDA 02**, sin modificar SENDA R6, que implemente realmente la propuesta visual azul en el `index.html` oficial y conserve toda la lógica funcional ya aprobada.

## Regla de aislamiento
- SENDA 02 vive en un repositorio/directorio propio.
- No se modifica, reemplaza ni elimina ningún archivo de SENDA R6.
- GitHub Pages de SENDA 02 publica únicamente su propio `index.html`.

## Navegación principal
**INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN**

## Propuesta visual obligatoria
- Cabecera azul oscuro con icono, nombre SENDA 02, navegación, botón INSTALAR SENDA y versión visible.
- Diseño compacto de escritorio basado en la propuesta visual aprobada: barra superior, panel lateral de carga/estadísticas/alarmas y área principal de trabajo.
- En móvil, navegación 2×2 y paneles apilados sin desbordamiento horizontal.
- Tarjetas KPI superiores: FOLIOS / FINCAS, PENDIENTES, EN REVISIÓN, FINALIZADOS y GESTIONES.
- Bloque compacto del trimestre actual y año.
- No usar ni mostrar "Expediente", `EXP-...`, "Número de finca" ni folios artificiales terminados en `-000`.

## INICIO
- Carga trimestral de archivos individuales, `.zip` y `.rar`.
- Mantener selector de año y trimestre.
- Inventario de última carga.
- Persistencia local del navegador.
- ZIP local; RAR con motor WebAssembly cuando sea necesario.

## INFORMACIÓN SENDA
- Vistas preservadas: Fincas/Folios, Movimientos, Segregaciones, Planos, Gravámenes, Históricos, Anotaciones, Jurídicas y Códigos.
- Filtros por año, trimestre, mes, cédula, FOLIO / FINCA, plano, nombre/apellidos.
- Alarmas y Códigos en la misma fila visual.
- Selección exclusiva de FOLIO / FINCA: al seleccionar uno, los demás se ocultan.
- Panel visual destacado del folio en revisión con acordeones/detalles.
- FINALIZAR REVISIÓN retira el folio de INFORMACIÓN SENDA y lo pasa a GESTIÓN.

## CONTROL
- Botones compactos homogéneos y con color activo: HIPOTECAS, GRAVÁMENES, SEGREGACIONES, ANOTACIONES, CÉDULAS JURÍDICAS, además de filtros y utilidades existentes.
- Cada FOLIO / FINCA aparece como acordeón compacto.
- Al seleccionar uno cambia de color y los demás se ocultan.
- El detalle seleccionado permanece en acordeón abierto.
- Acciones: GUARDAR FOLIO, ELIMINAR FOLIO, FINALIZADO, VER TODOS.

## GESTIÓN
- Folios finalizados con usuario, fecha/hora, observación y auditoría.
- Botón REGRESAR A INFORMACIÓN SENDA.
- Exportar BASE GESTIÓN en JSON y Excel con trámites realizados y gestiones correspondientes (Hipoteca, Gravamen, Segregación, Anotación, Jurídica, etc.).
- Importar JSON y Excel.
- Ningún folio puede aparecer simultáneamente como pendiente y finalizado.

## PWA / GitHub Pages
- Botón visible INSTALAR SENDA.
- Manifest, Service Worker, iconos y publicación GitHub Pages propios de SENDA 02.
- Service Worker con nombre de caché exclusivo de SENDA 02 para no heredar R6.
- Rutas relativas compatibles con `usuario.github.io/repositorio/`.

## Auditoría obligatoria
- Pruebas de estructura visual y funcional.
- Pruebas de flujo seleccionar → finalizar → gestión → regresar.
- Pruebas de CONTROL con acordeón, selección exclusiva y CÉDULAS JURÍDICAS activa por color.
- Pruebas RAR/ZIP e instalación.
- Prueba de aislamiento: SENDA R6 no cambia.
- Pruebas sobre el ZIP final extraído.
