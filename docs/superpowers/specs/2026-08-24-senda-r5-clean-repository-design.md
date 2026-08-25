# SENDA R5 — Repositorio limpio y funcional

## Objetivo
Crear un repositorio nuevo cuyo `index.html` sea la única interfaz oficial de SENDA, basado en el HTML funcional aprobado, sin interfaces paralelas ni recreaciones divergentes.

## Regla de preservación
Si un módulo, función, filtro, botón, vista, flujo o comportamiento existente funciona y el usuario no solicita explícitamente eliminarlo, se conserva. Las mejoras visuales no pueden mover, absorber, renombrar o suprimir funcionalidad.

## Navegación obligatoria
La navegación principal se mantiene exactamente en este orden:
1. INICIO
2. INFORMACIÓN SENDA
3. CONTROL
4. GESTIÓN

## INICIO
- Mantener la carga trimestral.
- Aceptar archivos `.xls`, `.txt`, `.csv`, `.json` y `.zip` compatibles.
- Mostrar año, trimestre, inventario de la última carga y acción de procesar/guardar.
- Identificar registros visibles por FOLIO / FINCA, nunca por números `EXP-*`.

## Identificación registral
- Formato visible: `PROVINCIA-NUMERO-DERECHO`, por ejemplo `4-200103-001`.
- FOLIO REAL y FINCA se tratan como el mismo identificador visible.
- No incluir cantón o distrito en el identificador visible.
- No inventar derecho `000` cuando la fuente no aporta un derecho identificable.
- Mantener el tipo de derecho separado como atributo: DOMINIO, USUFRUCTO, NUDA PROPIEDAD, HABITACIÓN, USO, USUFRUCTO CONJUNTO u otro derivado del catálogo.

## INFORMACIÓN SENDA
- Mantener filtros de Año, Trimestre, Mes del movimiento, Cédula, FOLIO / FINCA, Plano y Nombre/apellidos.
- Mantener ALARMAS y CÓDIGOS en una misma fila, cada uno como acordeón.
- Alarmas: amarillo para más de 2 meses de inactividad; rojo para 3 meses o más.
- Mantener agrupación/selección de códigos, Mostrar/Ocultar/MS y descarga por código.
- Restaurar las vistas registrales originales nunca solicitadas para eliminación: Fincas/Folios, Movimientos, Segregaciones, Planos, Gravámenes, Históricos, Anotaciones, Jurídicas y Códigos.
- Paginación: 25 registros en la primera página, 20 en las siguientes.
- Orden cronológico ascendente y “Sin fecha” al final.

## CONTROL
- Mantener filtros existentes y accesos rápidos Hipotecas, Gravámenes, Segregaciones, Anotaciones, Aplicar y Limpiar con coherencia visual.
- Abrir un solo FOLIO / FINCA por ficha.
- Mostrar tipo de derecho, plano, movimientos y color de alarma dentro de la ficha.
- Acciones obligatorias: GUARDAR FOLIO, ELIMINAR FOLIO y FINALIZADO.
- ELIMINAR FOLIO elimina sólo el estado de CONTROL/GESTIÓN del folio seleccionado; nunca elimina la fuente original.
- FINALIZADO transfiere sólo ese folio a GESTIÓN y conserva auditoría.
- Mantener historial de auditoría por folio y general.

## GESTIÓN
- Mostrar sólo folios finalizados/registrados.
- Mantener FOLIO / FINCA, tipo de derecho, usuario, fecha/hora y observación.
- Mantener filtros Mes del movimiento y Mes finalizado/registrado.
- Mantener importación y exportación de Gestión en el mismo módulo.
- Exportar JSON y Excel compatible.

## Persistencia y aplicación web
- Persistir estado operativo en `localStorage` del navegador.
- `index.html` es la fuente única de interfaz.
- Incluir `manifest.webmanifest` y `sw.js` para instalación PWA y uso sin conexión después de la primera carga.
- Usar el icono definitivo Propuesta 2, primera elección.

## Contratos de no regresión
La entrega falla si:
- Falta cualquiera de los cuatro módulos principales.
- Aparece una etiqueta visible “Expediente”, `EXP-2026-` o “Número de finca”.
- Falta INICIO o su carga trimestral.
- Falta cualquiera de Guardar/Eliminar/Finalizado.
- Falta el filtro de mes en SENDA, CONTROL o GESTIÓN.
- Alarmas y Códigos dejan de estar en la misma fila.
- Falta cualquiera de las vistas registrales originales enumeradas.
- El HTML del repositorio no es exactamente el `index.html` publicado.
