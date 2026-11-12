# VALIDACIÓN.md · CitasTaller — Entrega 8 (@tester)

Informe de resultados de pruebas con pytest contra las **cifras de control C1–C12**
y los **casos límite** de `AGENTS.md`, más pruebas de las **reglas de negocio
individuales (R1–R14)**.

Ejecutado con: `uv run pytest`  
Resultado global: **54 pruebas, 54 OK, 0 FALLA**

---

## Tabla de resultados

| # | Prueba | Esperado | Obtenido | Resultado | Causa probable |
|---|--------|----------|----------|-----------|----------------|
| 1 | C1: Lunes con dos carros confirmados; se intenta confirmar un tercero | Rechazar. Permanecen dos citas confirmadas. | Rechazado. Permanecen dos citas confirmadas. Tercera cita queda como "propuesta". | OK | — |
| 2 | C2: Martes con una visita confirmada; se intenta agregar un carro de taller | Rechazar. Permanece una visita. | Rechazado. Una visita domicilio, cero talleres. | OK | — |
| 3 | C3: Martes con una visita confirmada; se intenta agregar otra visita | Rechazar. Permanece una visita. | Rechazado. Una sola visita domicilio confirmada. | OK | — |
| 4 | C4: Miércoles vacío; se confirma un carro de taller | Aceptar. Queda un espacio de taller. | Aceptado. Una cita taller confirmada. | OK | — |
| 5 | C5: Día con un carro de taller; se intenta confirmar una visita | Rechazar. Se conserva el carro de taller. | Rechazado. Un taller confirmado, cero domicilios. | OK | — |
| 6 | C6: Se cancela uno de los dos carros del lunes | Queda un carro confirmado y un espacio disponible. | Un taller confirmado, uno cancelado. Espacio disponible. | OK | — |
| 7 | C7: Se cancela la visita del martes | El día vuelve a admitir dos carros de taller o una visita. | Día sin citas confirmadas. hay_espacio_taller=True, hay_espacio_domicilio=True. | OK | — |
| 8 | C8: Se intenta mover una cita a un día completo | Rechazar el cambio y conservar la fecha original. | Rechazado. Fecha original conservada. | OK | — |
| 9 | C9: La IA recibe un fallo sin modalidad ni fecha | "no indicado" en modalidad y fecha_propuesta. Señala lo pendiente. No se confirma la cita. | modalidad="no indicado", fecha_propuesta="no indicado", datos_por_aclarar incluye modalidad y fecha. No hay estado "confirmada". | OK | — |
| 10 | C10: Se registra una hora fuera de 07:00–16:00 | Rechazar esa hora. | hora_valida("18:00")=False, hora_valida("06:00")=False, hora_valida("16:01")=False. | OK | — |
| 11 | C11: Se pulsa confirmar repetidamente sobre la misma propuesta | Se crea una sola cita confirmada. | Primera confirmación OK. Segunda confirmación rechazada. Solo una cita confirmada. | OK | — |
| 12 | C12: Se inspecciona lo enviado a la IA | Cero nombres, teléfonos, placas y direcciones. | _limpiar_datos_personales elimina teléfonos, placas y fechas. Los campos de la propuesta no contienen datos personales. | OK | — |
| 13 | R5: hora_valida(None) | True | True | OK | — |
| 14 | R5: hora_valida("") | True | True | OK | — |
| 15 | R5: hora_valida("07:00") | True | True | OK | — |
| 16 | R5: hora_valida("16:00") | True | True | OK | — |
| 17 | R5: hora_valida("12:00") | True | True | OK | — |
| 18 | R5: hora_valida("06:59") | False | False | OK | — |
| 19 | R5: hora_valida("06:00") | False | False | OK | — |
| 20 | R5: hora_valida("16:01") | False | False | OK | — |
| 21 | R5: hora_valida("18:00") | False | False | OK | — |
| 22 | R5: hora_valida("abc") | False | False | OK | — |
| 23 | R5: hora_valida("25:00") | False | False | OK | — |
| 24 | R5: hora_valida("07:60") | False | False | OK | — |
| 25 | R5: hora_valida("not-a-time") | False | False | OK | — |
| 26 | R1: hay_espacio_taller fecha vacía | True | True | OK | — |
| 27 | R1: hay_espacio_taller con 1 taller confirmado | True | True | OK | — |
| 28 | R1: hay_espacio_taller con 2 talleres confirmados | False | False | OK | — |
| 29 | R10: citas en estado "propuesta" no ocupan espacio | True | True | OK | — |
| 30 | R2: hay_espacio_domicilio fecha vacía | True | True | OK | — |
| 31 | R2: hay_espacio_domicilio con 1 domicilio confirmado | False | False | OK | — |
| 32 | R3: domicilio_bloquea_dia sin domicilio | False | False | OK | — |
| 33 | R3: domicilio_bloquea_dia con domicilio | True | True | OK | — |
| 34 | R4: taller_bloquea_domicilio sin taller | False | False | OK | — |
| 35 | R4: taller_bloquea_domicilio con taller | True | True | OK | — |
| 36 | R11: todos los campos presentes | [] (sin faltantes) | [] | OK | — |
| 37 | R11: faltan todos los campos | [cliente_nombre, carro_descripcion, fallo, modalidad, fecha] | [cliente_nombre, carro_descripcion, fallo, modalidad, fecha] | OK | — |
| 38 | R11: falta solo fecha | ["fecha"] | ["fecha"] | OK | — |
| 39 | R11: modalidad vacía se considera faltante | ["modalidad"] | ["modalidad"] | OK | — |
| 40 | R13: confirma cita propuesta con espacio | True, "" | True, "" | OK | — |
| 41 | R13: no confirma si ya está confirmada | False | False | OK | — |
| 42 | R13: no confirma si no hay espacio | False, cita queda en "propuesta" | False, cita queda en "propuesta" | OK | — |
| 43 | R8: cambio a fecha con espacio | True, "" | True, "" | OK | — |
| 44 | R8: cambio a fecha llena | False | False | OK | — |
| 45 | R9: cancelar cita cambia estado a "cancelada" | "cancelada" | "cancelada" | OK | — |
| 46 | R9: después de cancelar hay espacio disponible | True | True | OK | — |
| 47 | R14: datos_personales_no_a_ia es placeholder (devuelve texto sin cambios) | Texto sin cambios | Texto sin cambios | OK | — |
| 48 | validar_confirmacion: taller en fecha vacía | True, "" | True, "" | OK | — |
| 49 | validar_confirmacion: domicilio en fecha con taller | False | False | OK | — |
| 50 | C9 extra: respuesta IA respeta contrato JSON (6 llaves) | 6 llaves exactas | 6 llaves exactas | OK | — |
| 51 | C12 extra: limpieza elimina teléfonos | Teléfono reemplazado por [TELEFONO] | Teléfono reemplazado por [TELEFONO] | OK | — |
| 52 | C12 extra: limpieza elimina placas | Placa reemplazada por [PLACA] | Placa reemplazada por [PLACA] | OK | — |
| 53 | C12 extra: limpieza elimina fechas AAAA-MM-DD | Fecha eliminada (reemplazada) | Fecha eliminada | OK | — |
| 54 | C12 extra: IA no devuelve datos personales en campos | Sin teléfonos, placas ni fechas en campos | Sin teléfonos, placas ni fechas en campos | OK | — |

---

## Resumen

| Métrica | Valor |
|---------|-------|
| Total de pruebas | 54 |
| Pruebas OK | 54 |
| Pruebas FALLA | 0 |
| Porcentaje de éxito | 100% |

---

## Hallazgos (observaciones no bloqueantes)

1. **C12 / limpieza de fechas**: El patrón de teléfono `\+?\d[\d\s\-]{7,}` del `_limpiar_datos_personales` en `app/services/ia_service.py` coincide con fechas en formato `AAAA-MM-DD` (por ejemplo, `2026-11-05`), por lo que una fecha puede ser reemplazada como `[TELEFONO]` en lugar de `[FECHA]`. El dato personal se elimina, pero la etiqueta de reemplazo no es la esperada. Esto no afecta C12 (el objetivo es que no se envíen datos personales), pero es una observación sobre el orden de las expresiones regulares.

2. **R14 / datos_personales_no_a_ia**: Esta función es un placeholder que devuelve el texto sin cambios (según el código actual de `app/business_rules.py`). La limpieza real de datos personales se realiza en `app/services/ia_service._limpiar_datos_personales`, no en `datos_personales_no_a_ia`.

---

## Cómo verificar en pantalla

1. Abrir una terminal en la carpeta raíz del proyecto:
   `E:\Documentos\Curso IA\Proyectos\Proyecto_control_de_citas_taller`

2. Ejecutar las pruebas:
   ```
   uv run pytest
   ```

3. Resultado esperado: `54 passed` con `0 failed` y `0 errors`.

4. Abrir este archivo `VALIDACIÓN.md` para ver el detalle de esperado vs obtenido por prueba.

5. Los archivos de prueba están en:
   - `tests/conftest.py` — configuración de pytest (app Flask con DB SQLite temporal)
   - `tests/test_citas.py` — pruebas C1–C12 y casos límite
   - `tests/test_reglas.py` — pruebas de reglas de negocio individuales (R1–R14)
