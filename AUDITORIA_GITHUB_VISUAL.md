# Auditoría profunda de visualización GitHub Pages — SENDA R5

**Versión auditada:** `SENDA-2026.08.24-R5-REPOSITORIO-LIMPIO-GITHUB-AUDITADO`

## Fuente única de interfaz

- `index.html` es la única interfaz HTML en la raíz.
- GitHub Pages publica la raíz exacta mediante `.github/workflows/pages.yml`.
- `.nojekyll` evita transformaciones de Jekyll.
- No existe un segundo HTML que pueda divergir visualmente.

## Regresiones bloqueadas

- Navegación obligatoria y en orden: **INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN**.
- INICIO conserva la carga trimestral y su inventario.
- INFORMACIÓN SENDA conserva filtros, Alarmas + Códigos y las vistas registrales originales.
- CONTROL conserva Guardar Folio, Eliminar Folio, Finalizado, filtros rápidos y auditoría.
- GESTIÓN conserva filtros, auditoría, importación JSON/Excel y exportación JSON/Excel.
- Descarga de la base SQLite preservada.
- No se forma ni se muestra un FOLIO / FINCA con Derecho `000`; esos registros quedan como **Sin folio real identificable**.

## Protección contra una versión vieja en GitHub

- El Service Worker se registra con `updateViaCache: 'none'`.
- Se ejecuta `reg.update()` en cada carga HTTP/HTTPS.
- El Service Worker usa estrategia network-first con `cache: 'reload'`.
- En activación elimina cachés `senda-*` anteriores.
- `controllerchange` provoca una única recarga segura para adoptar la nueva versión.
- El caché de esta entrega es `senda-r5-github-audit-v3`.

## Migración del navegador

Al iniciar, el sistema limpia datos y estados locales heredados que terminen en `-000`, conserva los estados válidos y reescribe `localStorage`. Esta migración se valida mediante `tests/js_logic_test.js`.

## Auditoría visual

Se verificó la composición estática real con Chromium en 1440×1000 y 390×844:

- Sin desbordamiento horizontal en INICIO, INFORMACIÓN SENDA, CONTROL ni GESTIÓN.
- En móvil los cuatro botones principales permanecen visibles en dos filas.
- INICIO mantiene el módulo de carga en su posición y formato.
- Icono definitivo presente.
- Alarmas y Códigos conservan la disposición aprobada.

## Barrera de publicación

GitHub Actions ejecuta antes del despliegue:

1. contrato de preservación Python;
2. contrato funcional JavaScript;
3. validación de sintaxis JavaScript;
4. comprobación de interfaz HTML única;
5. rechazo de etiquetas visibles heredadas no permitidas.

Si falla cualquiera de estas verificaciones, GitHub Pages no publica la entrega.
