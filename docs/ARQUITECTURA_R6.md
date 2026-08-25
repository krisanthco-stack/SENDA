# Arquitectura SENDA R6

## Fuente única

`index.html` es la única interfaz visual y funcional publicada por GitHub Pages.

## Navegación fija

1. INICIO
2. INFORMACIÓN SENDA
3. CONTROL
4. GESTIÓN

## Flujo por FOLIO / FINCA

- INFORMACIÓN SENDA mantiene únicamente folios pendientes.
- SELECCIONAR activa una revisión exclusiva y oculta los demás folios.
- FINALIZAR REVISIÓN crea un registro auditado de Gestión y retira el folio de pendientes.
- REGRESAR A INFORMACIÓN SENDA revierte el estado finalizado, conserva historial y vuelve a pendientes.
- El historial de Gestión conserva tipo de trámite, código, usuario, fechas y observaciones.

## Persistencia

El estado operativo se conserva en `localStorage`. Los datos fuente embebidos no se destruyen al eliminar o mover un folio entre estados.

## PWA y GitHub Pages

`manifest.webmanifest`, `sw.js` y `.github/workflows/pages.yml` publican e instalan la misma `index.html`. El Service Worker usa caché versionada R6 y estrategia network-first.
