# SENDA Registro Inmobiliario — R5

**Versión:** `SENDA-2026.08.24-R5-REPOSITORIO-LIMPIO-GITHUB-AUDITADO`

Este repositorio contiene una sola aplicación oficial: **`index.html` es la única fuente de verdad visual y funcional**. No existe un HTML alternativo ni una interfaz paralela que pueda quedar desincronizada.

## Módulos

La navegación principal se mantiene en este orden:

1. **INICIO** — carga trimestral de archivos o ZIP compatible e inventario de la última carga.
2. **INFORMACIÓN SENDA** — consulta, filtros, mes, alarmas, códigos, exportaciones y vistas registrales preservadas.
3. **CONTROL** — seguimiento por FOLIO / FINCA, alarmas por folio, Guardar, Eliminar y Finalizado con auditoría.
4. **GESTIÓN** — folios finalizados, auditoría, filtros, importación y exportación JSON/Excel.

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
