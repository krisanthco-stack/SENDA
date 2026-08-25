# Estándar obligatorio de entrega SENDA

## Regla prioritaria

**Si está bien y no se solicita eliminar, se mantiene.**

Una función, módulo, botón, filtro, vista, nombre, flujo o comportamiento existente no puede eliminarse, moverse, absorberse, sustituirse ni renombrarse por iniciativa del desarrollo. Sólo puede cambiarse cuando la solicitud lo indique expresamente.

## Fuente única

- `index.html` es la única interfaz oficial del repositorio.
- No se entrega un “HTML sincronizado” distinto de la aplicación publicada.
- Las mejoras visuales no pueden reacomodar la estructura funcional aprobada.

## Contrato de interfaz

Deben existir y mantenerse, en este orden:

**INICIO | INFORMACIÓN SENDA | CONTROL | GESTIÓN**

INICIO conserva carga trimestral e inventario. INFORMACIÓN SENDA conserva filtros, alarmas, códigos, exportaciones y vistas registrales. CONTROL conserva filtros y acciones por FOLIO / FINCA. GESTIÓN conserva auditoría, importación y exportación.

## Identificación

- Visible: **FOLIO / FINCA**.
- Formato: `PROVINCIA-NÚMERO-DERECHO`.
- No usar números artificiales `EXP-*`.
- No usar cantón/distrito en el identificador visible.
- No inventar Derecho `000` cuando el campo no viene informado.

## Verificación antes de entregar

1. Ejecutar todas las pruebas del repositorio.
2. Validar sintaxis JavaScript.
3. Buscar términos visibles prohibidos.
4. Confirmar que sólo exista un HTML raíz: `index.html`.
5. Crear ZIP sin `.git`, cachés ni archivos temporales.
6. Extraer el ZIP en una carpeta limpia.
7. Repetir pruebas y auditorías sobre esa extracción.
8. Sólo entonces declarar la entrega terminada.
