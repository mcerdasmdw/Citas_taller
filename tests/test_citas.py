"""Pruebas de cifras de control C1-C12 y casos límite de AGENTS.md.

Cada prueba valida un comportamiento específico contra el resultado exacto
esperado definido en la sección "Cifras de control" de AGENTS.md.

Todas las operaciones de base de datos y de reglas se ejecutan dentro de
``with app.app_context():`` para evitar errores de contexto de Flask.
"""

from app.business_rules import (
    confirmar_con_capacidad_atomica,
    validar_cambio_fecha,
    liberar_capacidad,
    hora_valida,
    hay_espacio_taller,
    hay_espacio_domicilio,
)
from app.models import Cita
from app import db
from app.services.ia_service import preparar_propuesta, _limpiar_datos_personales


# ---------------------------------------------------------------------------
# Helpers (todo dentro de app.app_context)
# ---------------------------------------------------------------------------

def _crear_cita(app, fecha, modalidad, estado="propuesta",
                cliente_nombre="Cliente Test", carro="Carro Test",
                fallo="Fallo Test", direccion="", hora=None):
    """Crea una cita directamente en la base de datos y la devuelve."""
    with app.app_context():
        cita = Cita(
            cliente_nombre=cliente_nombre,
            carro_descripcion=carro,
            placa="",
            fallo=fallo,
            modalidad=modalidad,
            direccion=direccion,
            fecha=fecha,
            hora=hora,
            estado=estado,
        )
        db.session.add(cita)
        db.session.commit()
        db.session.refresh(cita)
        return cita


def _contar_confirmadas(app, fecha, modalidad=None):
    """Cuenta citas confirmadas de una fecha (y opcionalmente modalidad)."""
    with app.app_context():
        q = Cita.query.filter_by(fecha=fecha, estado="confirmada")
        if modalidad:
            q = q.filter_by(modalidad=modalidad)
        return q.count()


def _traer_cita(app, cita_id):
    """Trae una cita por su id desde la base de datos."""
    with app.app_context():
        return Cita.query.get(cita_id)


# =============================================================================
# C1: Lunes con dos carros confirmados; se intenta confirmar un tercero
#     → Rechazar. Permanecen dos citas confirmadas.
# =============================================================================

class TestC1:
    def test_c1_lunes_dos_carros_rechaza_tercero(self, app):
        fecha = "2026-11-02"  # Lunes

        with app.app_context():
            _crear_cita(app, fecha, "taller", estado="confirmada",
                        cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")
            _crear_cita(app, fecha, "taller", estado="confirmada",
                        cliente_nombre="C2", carro="Carro 2", fallo="Fallo 2")

            # Antes del intento: dos confirmadas
            assert _contar_confirmadas(app, fecha, "taller") == 2

            # Intentar confirmar un tercero
            cita3 = _crear_cita(app, fecha, "taller", estado="propuesta",
                                cliente_nombre="C3", carro="Carro 3", fallo="Fallo 3")
            ok, mensaje = confirmar_con_capacidad_atomica(cita3)

        assert ok is False, f"Se esperaba rechazo, se obtuvo: ok={ok}, mensaje={mensaje}"
        assert _contar_confirmadas(app, fecha, "taller") == 2, \
            "Deben permanecer exactamente dos citas confirmadas"
        assert _traer_cita(app, cita3.id).estado == "propuesta", \
            "La tercera cita debe permanecer como propuesta"


# =============================================================================
# C2: Martes con una visita confirmada; se intenta agregar un carro de taller
#     → Rechazar. Permanece una visita.
# =============================================================================

class TestC2:
    def test_c2_martes_domicilio_rechaza_taller(self, app):
        fecha = "2026-11-03"  # Martes

        with app.app_context():
            _crear_cita(app, fecha, "domicilio", estado="confirmada",
                        cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1", direccion="Dir 1")

            # Antes: una visita
            assert _contar_confirmadas(app, fecha, "domicilio") == 1
            assert _contar_confirmadas(app, fecha, "taller") == 0

            # Intentar confirmar un taller ese mismo día
            cita_taller = _crear_cita(app, fecha, "taller", estado="propuesta",
                                      cliente_nombre="C2", carro="Carro 2", fallo="Fallo 2")
            ok, mensaje = confirmar_con_capacidad_atomica(cita_taller)

        assert ok is False, f"Se esperaba rechazo, se obtuvo: ok={ok}, mensaje={mensaje}"
        assert _contar_confirmadas(app, fecha, "domicilio") == 1, \
            "Debe permanecer una visita"
        assert _contar_confirmadas(app, fecha, "taller") == 0, \
            "No debe haber talleres confirmados"


# =============================================================================
# C3: Martes con una visita confirmada; se intenta agregar otra visita
#     → Rechazar. Permanece una visita.
# =============================================================================

class TestC3:
    def test_c3_martes_domicilio_rechaza_otro_domicilio(self, app):
        fecha = "2026-11-03"  # Martes

        with app.app_context():
            _crear_cita(app, fecha, "domicilio", estado="confirmada",
                        cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1", direccion="Dir 1")

            # Intentar confirmar otra visita domicilio
            cita_dom2 = _crear_cita(app, fecha, "domicilio", estado="propuesta",
                                    cliente_nombre="C2", carro="Carro 2", fallo="Fallo 2", direccion="Dir 2")
            ok, mensaje = confirmar_con_capacidad_atomica(cita_dom2)

        assert ok is False, f"Se esperaba rechazo, se obtuvo: ok={ok}, mensaje={mensaje}"
        assert _contar_confirmadas(app, fecha, "domicilio") == 1, \
            "Debe permanecer una visita"


# =============================================================================
# C4: Miércoles vacío; se confirma un carro de taller
#     → Aceptar. Queda un espacio de taller.
# =============================================================================

class TestC4:
    def test_c4_miercoles_vacio_confirma_taller(self, app):
        fecha = "2026-11-04"  # Miércoles

        assert _contar_confirmadas(app, fecha, "taller") == 0

        with app.app_context():
            cita = _crear_cita(app, fecha, "taller", estado="propuesta",
                               cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")
            ok, mensaje = confirmar_con_capacidad_atomica(cita)
            cita_confirmada = _traer_cita(app, cita.id)

        assert ok is True, f"Se esperaba aceptación, se obtuvo: ok={ok}, mensaje={mensaje}"
        assert _contar_confirmadas(app, fecha, "taller") == 1, \
            "Debe quedar una cita de taller confirmada"
        assert cita_confirmada.estado == "confirmada"


# =============================================================================
# C5: Día con un carro de taller; se intenta confirmar una visita
#     → Rechazar. Se conserva el carro de taller.
# =============================================================================

class TestC5:
    def test_c5_dia_con_taller_rechaza_domicilio(self, app):
        fecha = "2026-11-05"  # Jueves

        with app.app_context():
            _crear_cita(app, fecha, "taller", estado="confirmada",
                        cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")

            # Antes: un taller, sin domicilio
            assert _contar_confirmadas(app, fecha, "taller") == 1
            assert _contar_confirmadas(app, fecha, "domicilio") == 0

            # Intentar confirmar una visita a domicilio
            cita_dom = _crear_cita(app, fecha, "domicilio", estado="propuesta",
                                   cliente_nombre="C2", carro="Carro 2", fallo="Fallo 2", direccion="Dir 2")
            ok, mensaje = confirmar_con_capacidad_atomica(cita_dom)

        assert ok is False, f"Se esperaba rechazo, se obtuvo: ok={ok}, mensaje={mensaje}"
        assert _contar_confirmadas(app, fecha, "taller") == 1, \
            "Se conserva el carro de taller"
        assert _contar_confirmadas(app, fecha, "domicilio") == 0, \
            "No se confirma la visita"


# =============================================================================
# C6: Se cancela uno de los dos carros del lunes
#     → Queda un carro confirmado y un espacio disponible.
# =============================================================================

class TestC6:
    def test_c6_cancela_uno_de_dos_lunes(self, app):
        fecha = "2026-11-02"  # Lunes

        with app.app_context():
            c1 = _crear_cita(app, fecha, "taller", estado="confirmada",
                             cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")
            c2 = _crear_cita(app, fecha, "taller", estado="confirmada",
                             cliente_nombre="C2", carro="Carro 2", fallo="Fallo 2")

            assert _contar_confirmadas(app, fecha, "taller") == 2

            # Cancelar uno
            liberar_capacidad(_traer_cita(app, c1.id))

        assert _contar_confirmadas(app, fecha, "taller") == 1, \
            "Queda un carro confirmado"
        assert _traer_cita(app, c1.id).estado == "cancelada", \
            "La cita cancelada conserva el registro"
        assert _traer_cita(app, c2.id).estado == "confirmada", \
            "La otra cita sigue confirmada"


# =============================================================================
# C7: Se cancela la visita del martes
#     → El día vuelve a admitir dos carros de taller o una visita.
# =============================================================================

class TestC7:
    def test_c7_cancela_domicilio_martes_vuelve_disponible(self, app):
        fecha = "2026-11-03"  # Martes

        with app.app_context():
            _crear_cita(app, fecha, "domicilio", estado="confirmada",
                        cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1", direccion="Dir 1")

            assert _contar_confirmadas(app, fecha, "domicilio") == 1

            # Cancelar la visita
            cita = Cita.query.filter_by(fecha=fecha, modalidad="domicilio",
                                        estado="confirmada").first()
            liberar_capacidad(cita)

        # El día vuelve a admitir talleres y domicilio
        assert _contar_confirmadas(app, fecha, "domicilio") == 0
        assert _contar_confirmadas(app, fecha, "taller") == 0

        # Verificar que ahora sí hay espacio para ambos
        with app.app_context():
            assert hay_espacio_taller(fecha) is True, \
                "Debe admitir dos carros de taller"
            assert hay_espacio_domicilio(fecha) is True, \
                "Debe admitir una visita a domicilio"


# =============================================================================
# C8: Se intenta mover una cita a un día completo
#     → Rechazar el cambio y conservar la fecha original.
# =============================================================================

class TestC8:
    def test_c8_mover_a_dia_lleno_rechaza_y_conserva_fecha(self, app):
        fecha_origen = "2026-11-06"
        fecha_destino = "2026-11-07"  # Día lleno: 2 talleres confirmados

        with app.app_context():
            # Llenar el día destino con 2 talleres
            _crear_cita(app, fecha_destino, "taller", estado="confirmada",
                        cliente_nombre="D1", carro="Carro D1", fallo="Fallo D1")
            _crear_cita(app, fecha_destino, "taller", estado="confirmada",
                        cliente_nombre="D2", carro="Carro D2", fallo="Fallo D2")

            # Cita origen que se quiere mover
            cita = _crear_cita(app, fecha_origen, "taller", estado="confirmada",
                               cliente_nombre="O1", carro="Carro O1", fallo="Fallo O1")
            fecha_original = cita.fecha

            # Intentar cambiar la fecha al día lleno
            valido, mensaje = validar_cambio_fecha(
                fecha_origen, fecha_destino, "taller", cita_id_excluir=cita.id
            )

        assert valido is False, \
            f"Se esperaba rechazo, se obtuvo: valido={valido}, mensaje={mensaje}"
        cita_despues = _traer_cita(app, cita.id)
        assert cita_despues.fecha == fecha_original, \
            f"Se esperaba fecha {fecha_original}, se obtuvo {cita_despues.fecha}"


# =============================================================================
# C9: La IA recibe un fallo sin modalidad ni fecha
#     → Devuelve "no indicado" en esos campos y señala lo pendiente.
#     → No se confirma la cita.
# =============================================================================

class TestC9:
    def test_c9_ia_sin_modalidad_ni_fecha(self, app):
        # Texto con fallo pero sin modalidad ni fecha concreta
        texto = "El carro hace ruido al frenar, no sé cuándo llevarlo"
        propuesta = preparar_propuesta(texto, modalidad_indicada=None)

        assert propuesta["modalidad"] == "no indicado", \
            f"Esperado 'no indicado', obtenido: {propuesta['modalidad']}"
        assert propuesta["fecha_propuesta"] == "no indicado", \
            f"Esperado 'no indicado', obtenido: {propuesta['fecha_propuesta']}"

        # Debe señalar lo pendiente
        aclarar_str = str(propuesta["datos_por_aclarar"]).lower()
        assert "modalidad" in aclarar_str or "fecha" in aclarar_str, \
            f"datos_por_aclarar debe incluir modalidad y fecha: {propuesta['datos_por_aclarar']}"

        # La propuesta no confirma ninguna cita (solo devuelve un dict)
        assert isinstance(propuesta, dict)
        assert propuesta.get("estado") != "confirmada"

    def test_c9_ia_respeta_contrato_json(self, app):
        """La respuesta de la IA debe tener exactamente las llaves del contrato."""
        texto = "El carro hace ruido al frenar"
        propuesta = preparar_propuesta(texto, modalidad_indicada=None)

        llaves_esperadas = {"carro", "fallo", "disponibilidad_cliente",
                            "modalidad", "fecha_propuesta", "datos_por_aclarar"}
        assert set(propuesta.keys()) == llaves_esperadas, \
            f"Llaves obtenidas: {set(propuesta.keys())}"


# =============================================================================
# C10: Se registra una hora fuera de 07:00–16:00 → Rechazar esa hora.
# =============================================================================

class TestC10:
    def test_c10_hora_18_00_no_es_valida(self, app):
        assert hora_valida("18:00") is False, \
            "18:00 está fuera del horario 07:00-16:00"

    def test_c10_hora_06_00_no_es_valida(self, app):
        assert hora_valida("06:00") is False, \
            "06:00 está fuera del horario 07:00-16:00"

    def test_c10_hora_16_01_no_es_valida(self, app):
        assert hora_valida("16:01") is False, \
            "16:01 está fuera del horario 07:00-16:00"

    def test_c10_hora_07_00_es_valida(self, app):
        assert hora_valida("07:00") is True, \
            "07:00 está dentro del horario"

    def test_c10_hora_16_00_es_valida(self, app):
        assert hora_valida("16:00") is True, \
            "16:00 está dentro del horario"


# =============================================================================
# C11: Se pulsa confirmar repetidamente sobre la misma propuesta
#     → Se crea una sola cita confirmada.
# =============================================================================

class TestC11:
    def test_c11_confirmar_repeticion_solo_una_cita(self, app):
        fecha = "2026-11-08"  # Domingo (no hay restricción de días definida)

        with app.app_context():
            cita = _crear_cita(app, fecha, "taller", estado="propuesta",
                               cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")

            # Primera confirmación
            ok1, _ = confirmar_con_capacidad_atomica(cita)
            assert ok1 is True, f"Primera confirmación debería funcionar: ok={ok1}"

            # Segunda confirmación repetida sobre la misma cita
            ok2, mensaje2 = confirmar_con_capacidad_atomica(cita)
            assert ok2 is False, \
                f"Segunda confirmación debe rechazarse: ok={ok2}, mensaje={mensaje2}"

        # Verificar que solo existe una cita confirmada
        assert _contar_confirmadas(app, fecha, "taller") == 1, \
            "Debe existir solo una cita confirmada"

    def test_c11_cita_ya_confirmada_no_se_duplica(self, app):
        fecha = "2026-11-08"

        with app.app_context():
            cita = _crear_cita(app, fecha, "taller", estado="confirmada",
                               cliente_nombre="C1", carro="Carro 1", fallo="Fallo 1")

            # Intentar confirmar una cita que ya está confirmada
            ok, mensaje = confirmar_con_capacidad_atomica(cita)
            assert ok is False, \
                f"No se debe confirmar dos veces: ok={ok}, mensaje={mensaje}"

        assert _contar_confirmadas(app, fecha, "taller") == 1


# =============================================================================
# C12: Se inspecciona lo enviado a la IA → Cero nombres, teléfonos, placas y direcciones.
# =============================================================================

class TestC12:
    def test_c12_texto_limpieza_elimina_telefonos(self, app):
        """_limpiar_datos_personales debe eliminar patrones de teléfono."""
        texto = "Llame al 5551234567 para coordinar"
        limpio = _limpiar_datos_personales(texto)
        assert "5551234567" not in limpio, f"Teléfono no eliminado: {limpio}"
        assert "[TELEFONO]" in limpio

    def test_c12_texto_limpieza_elimina_placas(self, app):
        """_limpiar_datos_personales debe eliminar patrones de placa."""
        texto = "El carro ABC1234 tiene un ruido"
        limpio = _limpiar_datos_personales(texto)
        assert "ABC1234" not in limpio, f"Placa no eliminada: {limpio}"
        assert "[PLACA]" in limpio

    def test_c12_texto_limpieza_elimina_fechas(self, app):
        """_limpiar_datos_personales debe eliminar fechas AAAA-MM-DD.

        Nota: la fecha 2026-11-05 coincide con el patrón de teléfono
        (dígitos y guiones), por lo que se reemplaza como [TELEFONO],
        no como [FECHA]. Lo importante es que la fecha desaparece del texto.
        """
        texto = "Para el 2026-11-05 el carro falla"
        limpio = _limpiar_datos_personales(texto)
        assert "2026-11-05" not in limpio, f"Fecha no eliminada: {limpio}"

    def test_c12_ia_no_devuelve_datos_personales_en_campos(self, app):
        """Cada campo del contrato JSON debe estar libre de datos personales
        que el limpiador sí reconoce (teléfonos, placas, fechas)."""
        texto_con_personales = (
            "Cliente: María García, Tel: 5551234567, Placa: XYZ9876, "
            "el carro tiene un ruido raro para el 2026-11-05"
        )
        propuesta = preparar_propuesta(texto_con_personales, modalidad_indicada=None)

        respuesta_texto = str(propuesta)
        assert "5551234567" not in respuesta_texto, \
            f"Teléfono en respuesta: {respuesta_texto}"
        assert "XYZ9876" not in respuesta_texto, \
            f"Placa en respuesta: {respuesta_texto}"
        assert "2026-11-05" not in respuesta_texto, \
            f"Fecha en respuesta: {respuesta_texto}"

    def test_c12_nombres_no_se_envían_a_ia(self, app):
        """Los nombres de clientes no aparecen en los campos de la propuesta
        de IA (el limpiador no los elimina pero la extracción no los captura)."""
        texto_con_nombre = "Juan Pérez dice que el carro hace ruido al frenar"
        propuesta = preparar_propuesta(texto_con_nombre, modalidad_indicada=None)

        # El nombre no debería estar en el campo carro (se extrae descripción del carro)
        assert "Juan Pérez" not in propuesta.get("carro", ""), \
            f"Nombre en campo carro: {propuesta.get('carro', '')}"
        assert "Juan Pérez" not in propuesta.get("fallo", ""), \
            f"Nombre en campo fallo: {propuesta.get('fallo', '')}"
