# Diseño: INFORMACIÓN SENDA, CONTROL y GESTIÓN

## Objetivo
Ampliar la aplicación Streamlit existente sin alterar su motor registral: INFORMACIÓN SENDA carga y organiza cortes trimestrales y alarmas; CONTROL consulta expedientes por número de finca y procesa trámites; GESTIÓN conserva exclusivamente trámites registrados con auditoría e intercambio JSON/Excel.

## Reglas preservadas
- Mantener `read_tabular_upload`, `normalize_dataset`, `classify`, `planos_sin_finca` y la traducción de catálogos existentes.
- Mantener aceptación de archivos `.xls` tabulados y `.txt`.
- Mantener las vistas registrales existentes, ahora dentro de INFORMACIÓN SENDA.

## Navegación
Navegación horizontal superior: `INFORMACIÓN SENDA | CONTROL | GESTIÓN`.

## INFORMACIÓN SENDA
- Carga de archivos individuales o ZIP, asociados a año y trimestre T1-T4.
- Búsqueda por cédula, nombre, primer apellido, segundo apellido, finca, folio, plano, código y operación.
- Si hay nombres/apellidos repetidos, mostrar todas las coincidencias con cédula y finca.
- Lista de códigos agrupada. Selector de código activo y modos `Mostrar`, `Ocultar`, `MS (Mostrar Seleccionado)`.
- Descarga por código en Excel y JSON.
- Resultados en acordeón: 25 registros en página 1; 20 en páginas posteriores.
- Alarmas: amarillo >60 días y <90; rojo >=90 días sin movimiento; registrado no aparece como pendiente.

## CONTROL
- Trabaja sobre movimientos pendientes.
- Orden por defecto antiguo a reciente.
- Filtros por fechas, expediente/finca, folio, cédula, nombre/apellidos, plano, código y tipos (hipotecas, gravámenes, segregaciones, anotaciones, etc.).
- Expediente visible identificado por `NUMERO` de finca; mantiene `FINCA_ID` completo internamente.
- Al seleccionar expediente, mostrar datos generales y secciones por tipo. Si hay varios movimientos del mismo tipo, mostrar cantidad y todos los asientos.
- Acción `REGISTRADO` requiere operador y permite observación.
- Al registrar: persistir quién, cuándo, observación; excluir de pendientes; transferir a GESTIÓN.
- CONTROL incluye historial de registro para consultar quién/cuándo registró.

## GESTIÓN
- Sólo movimientos registrados.
- Mostrar `registrado_por`, `registrado_en`, observación e historial de auditoría.
- Filtros por finca/expediente, folio, cédula, nombre/apellidos, código, fecha de movimiento y fecha de registro.
- Importación y exportación JSON/Excel en el mismo módulo.
- Importación idempotente por `MOVIMIENTO_ID`.

## Persistencia
SQLite local `data/registro_inmobiliario.db`.
- `movimientos`: base consolidada para cortes cargados.
- `gestion_registrados`: estado registrado + auditoría básica.
- `auditoria`: eventos de registro/importación.
- Tablas normalizadas por fuente se guardan también con columnas `ANIO`, `TRIMESTRE`, `LOTE_ID` para reproducir la organización analítica.

## Seguridad de datos
- No inventar fechas faltantes.
- Conservar fuente, corte, código y descripción originales.
- No convertir alertas analíticas en conclusiones jurídicas.
