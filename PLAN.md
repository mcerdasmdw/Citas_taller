# PLAN.md · CitasTaller

Plan de entregas del MVP, organizado por bloques para los subagentes @arquitecto, @backend, @frontend, @tester y @revisor.

---

## 1. RESUMEN

Vamos a construir una app web en español para crear y controlar citas de revisión de carros (taller y domicilio). El usuario ingresa manualmente los datos recibidos por WhatsApp en un formulario. El agente de IA interpreta la solicitud (sin datos personales) y devuelve un contrato JSON con carro, fallo, disponibilidad, modalidad, fecha propuesta y datos por aclarar. El código aplica reglas de capacidad (máx. 2 carros/día taller o 1 visita/día), valida y guarda en SQLite local. Sale: citas confirmadas en calendario, detalle de cada cita, disponibilidad por día y propuestas de IA revisadas por el usuario.

---

## 2. LO QUE ENCONTRÉ

### En `contexto/`
- `Contexto_Mi_App.md`: documento de contexto completo (251 líneas) con reglas R1–R14, contrato JSON del agente, cifras de control C1–C12, casos límite y reglas del sistema (Flask + MVC + uv + SQLite local).
- `Contexto.md`: original, idéntico al anterior.

### En `insumos/`
- `Control_citas_Taller.xlsx`: solo referencia, no se importa.
  - Hoja `Citas`: 101 filas (1 encabezado + 100 datos) × 22 columnas (cita_id, cliente_id, cliente_nombre, cliente_telefono, cliente_email, vehiculo_id, placa, marca, modelo, anio, kilometraje, fecha_cita, hora_inicio, hora_fin, duracion_minutos, servicio, mecanico_id, estado, canal_reserva, costo_estimado, moneda, observaciones).
  - Hoja `Guia`: 14 filas × 2 columnas, describe el archivo (100 citas ficticias, noviembre 2026, 4 mecánicos, estados, etc.).

### ¿Coincide con AGENTS.md?
Parcialmente. AGENTS.md ya integra los insumos como referencia y añade modalidad (taller/domicilio) como campo nuevo. Los estados del Excel (pendiente, en_proceso, completada, no_asistio) se registran pero solo `confirmada` consume capacidad.

### Qué falta o no cuadra
- El proveedor y modelo de IA están pendientes (AGENTS.md punto 14): se usará **modo simulado** hasta definirlo (confirmado por el usuario).
- Teléfono y placa son opcionales. **Dirección es obligatoria** para visitas a domicilio (confirmado por el usuario).
- Estados de cita: los 7 estados del contexto y del Excel (`propuesta`, `confirmada`, `cancelada`, `pendiente`, `en_proceso`, `completada`, `no_asistio`); solo `confirmada` consume capacidad.
- Días de atención, feriados y cierres especiales no están definidos: no se inventan restricciones.
- No hay archivo de importación del Excel en la app: solo es referencia histórica.
- Se cargarán **fechas de prueba precargadas** inicialmente para verificar las cifras C1–C4 (confirmado por el usuario).

---

## 3. ENTREGAS POR SUBAGENTE

| N° | Responsable | Qué debe entregar | Archivos que crea o modifica | Qué recibe de la entrega anterior | Cómo se verifica en pantalla |
|----|-------------|-------------------|------------------------------|-----------------------------------|------------------------------|
| 1 | @backend | Estructura MVC base con uv: `app/__init__.py` con `create_app()`, `app/models.py` con modelo `Cita` (SQLite) con 7 estados (`propuesta`, `confirmada`, `cancelada`, `pendiente`, `en_proceso`, `completada`, `no_asistio`) y `direccion` obligatoria, `app/business_rules.py` con reglas R1, R2, R3, R4 (capacidad), `app/services/ia_service.py` con contrato JSON simulado (modo simulado), `pyproject.toml`, `.env`, `.gitignore`, `iniciar_app.bat`, script de cargado de fechas de prueba iniciales | `app/__init__.py`, `app/models.py`, `app/business_rules.py`, `app/services/ia_service.py`, `pyproject.toml`, `.env`, `.gitignore`, `iniciar_app.bat`, `app/data/seed.py` | AGENTS.md, PLAN.md, contexto/ | Doble clic en `iniciar_app.bat`; se abre `http://127.0.0.1:5000/` y muestra el calendario con fechas de prueba precargadas |
| 2 | @backend | Reglas R5 (hora 07:00–16:00), R6 (IA no confirma sin usuario), R7 (re-consulta capacidad antes de confirmar), R8 (cambio de fecha verifica nuevo día), R9 (cancelar libera capacidad), R10 (propuestas no consumen), R11 (campos requeridos: cliente, carro, fallo, modalidad, fecha), R13 (operación atómica), R14 (privacidad) | `app/business_rules.py` (se agregan funciones) | Entrega 1 (modelo Cita y base de reglas) | En el formulario, intentar registrar hora 18:00 → rechaza con mensaje "entre 07:00 y 16:00" |
| 3 | @backend | Rutas de citas: crear (estado propuesta), confirmar (valida R7/R13), cambiar fecha (valida R8), cancelar (R9), lista, API disponibilidad por fecha. Dirección obligatoria en el formulario. | `app/controllers/citas.py`, `app/templates/calendario.html`, `app/templates/formulario_cita.html`, `app/templates/detalle_cita.html` | Entrega 2 (reglas de negocio) | Abrir `/citas/nueva`, crear cita taller para hoy con dirección, confirmar, ver en calendario con estado "confirmada" |
| 4 | @frontend | Pantalla de inicio con bienvenida y navegación; estilo base oscuro con CSS en `base.html` | `app/templates/base.html`, `app/templates/inicio.html` | Entrega 3 (rutas de citas) | Abrir `/` y ver título "CitasTaller", menú con Calendario / Nueva cita / Lista de citas |
| 5 | @frontend | Pantalla de resultados/calendario con contadores grandes (todas, confirmadas, pendientes, canceladas) y tabla con filtro de búsqueda | `app/templates/calendario.html` (mejorada) | Entrega 4 (base e inicio) | Abrir `/` → ver 4 contadores grandes arriba y tabla de citas con campo de filtro |
| 6 | @frontend | Detalle por registro: botones Confirmar / Cambiar fecha / Cancelar según los 7 estados | `app/templates/detalle_cita.html` (mejorada) | Entrega 3 y 5 | Abrir detalle de una cita propuesta → ver botón "Confirmar cita"; al confirmar, estado cambia a "confirmada" y se libera/consume capacidad |
| 7 | @frontend | Propuesta de IA: pantalla que muestra los 6 campos del contrato JSON y botón para copiar al formulario | `app/templates/propuesta_ia.html`, `app/controllers/ia.py` (rutas de IA) | Entrega 3 y 1 (contrato JSON) | Abrir `/ia/preparar` con texto de prueba → ver JSON interpretado con "no indicado" en campos faltantes |
| 8 | @tester | Pruebas en `tests/` con pytest contra cifras de control C1–C12 y casos límite; `VALIDACIÓN.md` con esperado vs obtenido | `tests/test_citas.py`, `tests/test_reglas.py`, `VALIDACIÓN.md` | Entrega 3 (rutas y reglas) | Ejecutar `uv run pytest` → ver cuántas pruebas pasan y cuántas fallan, con tabla en `VALIDACIÓN.md` |
| 9 | @revisor | Revisión de seguridad: llaves en `.env` (no en código), datos personales no expuestos, `.gitignore` cubre `.env` y `.db`, nada fuera de AGENTS.md | Informe de hallazgos (no modifica código) | Entrega 1–8 | Ver informe del revisor con prioridad Alta/Media/Baja y correcciones propuestas |

---

## 4. PUNTOS DE CONTROL

| Después de la entrega | Quiere interviene | Qué debe ver el usuario en pantalla (resultado exacto) |
|-----------------------|-------------------|--------------------------------------------------------|
| 1 | @tester | Calendario vacío en `http://127.0.0.1:5000/`; mensaje "No hay citas registradas" |
| 2 | @tester | Intentar hora 18:00 → alerta "La hora debe estar entre 07:00 y 16:00" |
| 3 | @tester | Crear 2 citas taller el mismo día y confirmar ambas → intento de tercera se rechaza: "No hay espacio de taller disponible" |
| 5 | @tester | Calendario muestra 4 contadores grandes: total, confirmadas, pendientes, canceladas; tabla con filtro funcional |
| 8 | @revisor | `VALIDACIÓN.md` muestra todas las cifras C1–C12 con resultado OK o FALLA con causa probable |
| 9 | — | Informe del revisor sin hallazgos de prioridad Alta; .gitignore cubre `.env` y `*.db` |

---

## 5. RIESGOS

| Riesgo | Qué hará cada subagente |
|--------|-------------------------|
| Datos incompletos (falta fallo, fecha o modalidad) | @backend: valida R11 y bloquea confirmación con mensaje claro. @frontend: muestra campos obligatorios marcados en el formulario. |
| Archivos escaneados o PDF | @backend: no implementa lectura de archivos (según AGENTS.md caso límite). @frontend: muestra mensaje "ingreso manual requerido". @tester: prueba que no se intente leer PDF. |
| Respuesta del agente de IA que no es JSON válido | @backend: `validar_respuesta_ia()` rechaza y no crea cita automáticamente. @tester: prueba con JSON inválido y verifica que la app no se rompa. |
| Llave de IA gratis con límite o sin proveedor definido | @backend: usa modo simulado (llave en `.env`, proveedor "simulado"). @revisor: verifica que la llave no esté escrita en el código. @tester: verifica que la app funcione sin IA (modo manual). |
| Contradicción entre Excel y AGENTS.md | @arquitecto: documenta en PLAN.md y pregunta al usuario antes de asumir. Nadie inventa reglas. |

---

## 6. PREGUNTAS PARA MÍ (respondidas)

Todas las preguntas han sido confirmadas:

1. Excel: **solo referencia**, no se importa en la app.
2. Estados: **los 7 estados** (contexto + Excel): `propuesta`, `confirmada`, `cancelada`, `pendiente`, `en_proceso`, `completada`, `no_asistio`. Solo `confirmada` consume capacidad.
3. Dirección: **obligatoria** para visitas a domicilio.
4. IA: **modo simulado** hasta definir el proveedor real.
5. Fechas: **precargadas** inicialmente para verificar C1–C4.

---

**Estado:** Plan listo y aprobado. Los subagentes pueden empezar a construir siguiendo el orden de entregas (1 → 9).

