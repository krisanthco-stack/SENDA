# SENDA Registro Inmobiliario — R6

**Versión:** `SENDA-2026.08.25-R6-REVISION-FOLIO-GESTION`

Este repositorio contiene una sola aplicación oficial: **`index.html` es la única fuente de verdad visual y funcional**. No existe un HTML alternativo ni una interfaz paralela que pueda quedar desincronizada.

## Módulos

La navegación principal se mantiene en este orden:

1. **INICIO** — carga trimestral de archivos individuales, RAR o ZIP e inventario de la última carga.
2. **INFORMACIÓN SENDA** — consulta, filtros, mes, alarmas, códigos, vistas registrales preservadas y selección exclusiva de un FOLIO / FINCA para revisión.
3. **CONTROL** — seguimiento por FOLIO / FINCA, botones compactos de Hipotecas, Gravámenes, Segregaciones, Anotaciones y Cédulas Jurídicas, con estado activo por color; Guardar, Eliminar y Finalizado con auditoría.
4. **GESTIÓN** — folios finalizados, REGRESAR A INFORMACIÓN SENDA, auditoría, filtros, importación JSON/Excel y base histórica de trámites realizados en JSON/Excel.

## Identificación registral

La identificación visible es **FOLIO / FINCA**, formada como `PROVINCIA-NÚMERO-DERECHO`, por ejemplo `4-200103-001`. Cantón y distrito no forman parte del identificador visible. Si una carga no aporta Derecho suficiente, el sistema no inventa `000`; muestra el registro como **Sin folio real identificable**.

## Ejecutar localmente

No requiere dependencias de aplicación. Con Python 3:

```bash
python serve.py
```

Luego abra `http://127.0.0.1:8000/index.html`.

También puede indicar otro puerto:

```bash
python serve.py --port 8080
```

> Abrir `index.html` directamente como archivo permite usar la mayor parte de la aplicación, pero la instalación PWA y el Service Worker requieren HTTP/HTTPS.

## Publicar en GitHub Pages

El repositorio incluye `.github/workflows/pages.yml`. En **Settings → Pages → Source** seleccione **GitHub Actions**. Cada `push` a `main` ejecuta primero las pruebas y la auditoría de interfaz; sólo si pasan, GitHub Pages publica **la raíz exacta del repositorio**, donde `index.html` es la única interfaz. No copie ni genere otro HTML.

`.nojekyll` evita transformaciones innecesarias de Jekyll. El Service Worker fuerza actualización de red y elimina cachés SENDA anteriores para que una versión vieja no siga apareciendo después de publicar una versión nueva.

## Instalación PWA

Al publicarse por HTTP/HTTPS, `manifest.webmanifest` y `sw.js` permiten instalar SENDA como aplicación. El Service Worker usa estrategia **network-first con recarga de caché HTTP**, `updateViaCache: none`, `skipWaiting`, `clients.claim` y limpieza de cachés SENDA anteriores. Esto reduce el riesgo de que GitHub Pages muestre una interfaz vieja después de una actualización.

## Persistencia

Los cambios operativos de CONTROL/GESTIÓN y las cargas adicionales se guardan en `localStorage` del navegador. No se elimina el archivo fuente embebido al usar **ELIMINAR FOLIO**; esa acción sólo retira el folio de las vistas operativas.

## Datos

El HTML incluye los registros base utilizados por la versión funcional de referencia. Las cargas nuevas se procesan localmente en el navegador. Los `.xls` registrales de SENDA que son texto tabulado se leen como texto; ZIP usa las capacidades de descompresión disponibles en navegadores modernos.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Para validar JavaScript inline se extrae el bloque `<script>` y se ejecuta `node --check`; la auditoría de entrega también repite las pruebas sobre el ZIP extraído.

## Regla principal de preservación

Consulte `DELIVERY_STANDARD.md`. La regla obligatoria es: **si una función está bien y no se solicita explícitamente eliminarla, se mantiene**.


## Carga comprimida RAR y ZIP

El módulo **INICIO** acepta archivos individuales, `.zip` y `.rar` sin cambiar la estructura visual aprobada. ZIP usa primero el extractor nativo incluido en `index.html`; si el método de compresión no es compatible, y para RAR, se utiliza `7z-wasm@1.2.0` (7-Zip WebAssembly) fijado a una versión concreta. El motor se carga desde jsDelivr en la primera utilización y el Service Worker lo guarda en caché para reutilizarlo. Los archivos se procesan en el navegador; SENDA no los envía a un servidor propio.

## Instalación de SENDA

El encabezado incluye **INSTALAR SENDA**. En navegadores con soporte PWA usa el evento nativo `beforeinstallprompt`; en Safari/iOS muestra la ruta **Compartir → Añadir a pantalla de inicio**. La aplicación conserva `index.html` como única interfaz oficial.

## Dependencia de descompresión

RAR y el respaldo ZIP usan `7z-wasm` versión 1.2.0, proyecto de `use-strict/7z-wasm`, con licencia GNU LGPL y la restricción unRAR indicada por el propio proyecto. La dependencia está referenciada por URL versionada; no se modifica ni se utiliza para crear archivos RAR.

## Flujo de revisión R6

- En **INFORMACIÓN SENDA**, **SELECCIONAR** fija un único FOLIO / FINCA en revisión y oculta los demás resultados mientras esa selección está activa.
- **FINALIZAR REVISIÓN DEL FOLIO / FINCA** retira ese folio de pendientes y lo traslada a **GESTIÓN**, conservando movimientos, tipo de derecho, código, tipo de gestión, usuario, fecha/hora y observación.
- En **GESTIÓN**, **REGRESAR A INFORMACIÓN SENDA** revierte el estado sin destruir el historial y deja trazabilidad de la devolución.
- **BASE GESTIÓN JSON** y **BASE GESTIÓN EXCEL** exportan trámites realizados y las gestiones asociadas, incluyendo Hipotecas, Gravámenes, Segregaciones, Anotaciones y otras categorías detectadas.
- Un FOLIO / FINCA no puede figurar simultáneamente como pendiente y finalizado.

## Icono R6

El único icono oficial es `assets/app_icon_senda_r6.png`. Lo usan el encabezado, el manifiesto PWA, el Service Worker y la instalación desde GitHub Pages.
