"""Pruebas unitarias de reglas de negocio (R1-R14, R5/hora_valida, etc.).

Todas las operaciones de base de datos se realizan dentro de
``with app.app_context():`` para evitar ``RuntimeError`` por contexto
fuera de la aplicación.
"""

from app.business_rules import (
    hora_valida,
    hay_espacio_taller,
    hay_espacio_domicilio,
    domicilio_bloquea_dia,
    taller_bloquea_domicilio,
    campos_requeridos_para_confirmar,
    confirmar_con_capacidad_atomica,
    validar_cambio_fecha,
    liberar_capacidad,
    datos_personales_no_a_ia,
    validar_confirmacion,
)
from app.models import Cita
from app import db


# =============================================================================
# R5: hora_valida — la hora debe estar entre 07:00 y 16:00 si se registra
# =============================================================================

class TestHoraValida:
    """R5: validación de hora de atención."""

    def test_hora_none_es_valida(self, app):
        assert hora_valida(None) is True

    def test_hora_vacia_es_valida(self, app):
        assert hora_valida("") is True

    def test_hora_07_00_limite_inferior_es_valida(self, app):
        assert hora_valida("07:00") is True

    def test_hora_16_00_limite_superior_es_valida(self, app):
        assert hora_valida("16:00") is True

    def test_hora_12_00_es_valida(self, app):
        assert hora_valida("12:00") is True

    def test_hora_antes_de_07_00_no_es_valida(self, app):
        assert hora_valida("06:59") is False
        assert hora_valida("06:00") is False

    def test_hora_despues_de_16_00_no_es_valida(self, app):
        assert hora_valida("16:01") is False
        assert hora_valida("18:00") is False

    def test_hora_formato_invalido_no_es_valida(self, app):
        assert hora_valida("abc") is False
        assert hora_valida("25:00") is False
        assert hora_valida("07:60") is False
        assert hora_valida("not-a-time") is False


# =============================================================================
# R1: hay_espacio_taller — máximo 2 carros de taller por día
# =============================================================================

class TestHayEspacioTaller:
    """R1: capacidad de taller por día."""

    def test_fecha_vacia_tiene_espacio_taller(self, app):
        with app.app_context():
            assert hay_espacio_taller("2026-11-04") is True

    def test_fecha_con_un_taller_tiene_espacio(self, app):
        with app.app_context():
            db.session.add(Cita(
                cliente_nombre="Cliente 1",
                carro_descripcion="Carro 1",
                fallo="Fallo 1",
                modalidad="taller",
                direccion="",
                fecha="2026-11-04",
                estado="confirmada",
            ))
            db.session.commit()
            assert hay_espacio_taller("2026-11-04") is True

    def test_fecha_con_dos_talleres_no_tiene_espacio(self, app):
        with app.app_context():
            db.session.add_all([
                Cita(
                    cliente_nombre="Cliente 1",
                    carro_descripcion="Carro 1",
                    fallo="Fallo 1",
                    modalidad="taller",
                    direccion="",
                    fecha="2026-11-04",
                    estado="confirmada",
                ),
                Cita(
                    cliente_nombre="Cliente 2",
                    carro_descripcion="Carro 2",
                    fallo="Fallo 2",
                    modalidad="taller",
                    direccion="",
                    fecha="2026-11-04",
                    estado="confirmada",
                ),
            ])
            db.session.commit()
            assert hay_espacio_taller("2026-11-04") is False

    def test_citas_propuesta_no_ocupan_espacio_taller(self, app):
        """R10: las propuestas no consumen capacidad."""
        with app.app_context():
            db.session.add_all([
                Cita(
                    cliente_nombre="Cliente 1",
                    carro_descripcion="Carro 1",
                    fallo="Fallo 1",
                    modalidad="taller",
                    direccion="",
                    fecha="2026-11-04",
                    estado="propuesta",
                ),
                Cita(
                    cliente_nombre="Cliente 2",
                    carro_descripcion="Carro 2",
                    fallo="Fallo 2",
                    modalidad="taller",
                    direccion="",
                    fecha="2026-11-04",
                    estado="propuesta",
                ),
            ])
            db.session.commit()
            assert hay_espacio_taller("2026-11-04") is True


# =============================================================================
# R2: hay_espacio_domicilio — máximo 1 visita a domicilio por día
# =============================================================================

class TestHayEspacioDomicilio:
    """R2: capacidad de domicilio por día."""

    def test_fecha_vacia_tiene_espacio_domicilio(self, app):
        with app.app_context():
            assert hay_espacio_domicilio("2026-11-04") is True

    def test_fecha_con_un_domicilio_no_tiene_espacio(self, app):
        with app.app_context():
            db.session.add(Cita(
                cliente_nombre="Cliente 1",
                carro_descripcion="Carro 1",
                fallo="Fallo 1",
                modalidad="domicilio",
                direccion="Dir 1",
                fecha="2026-11-04",
                estado="confirmada",
            ))
            db.session.commit()
            assert hay_espacio_domicilio("2026-11-04") is False


# =============================================================================
# R3: domicilio_bloquea_dia — una visita a domicilio bloquea todo el día
# =============================================================================

class TestDomicilioBloqueaDia:
    """R3: domicilio confirmado bloquea cualquier otra cita ese día."""

    def test_fecha_sin_domicilio_no_bloquea(self, app):
        with app.app_context():
            assert domicilio_bloquea_dia("2026-11-04") is False

    def test_fecha_con_domicilio_bloquea(self, app):
        with app.app_context():
            db.session.add(Cita(
                cliente_nombre="Cliente 1",
                carro_descripcion="Carro 1",
                fallo="Fallo 1",
                modalidad="domicilio",
                direccion="Dir 1",
                fecha="2026-11-04",
                estado="confirmada",
            ))
            db.session.commit()
            assert domicilio_bloquea_dia("2026-11-04") is True


# =============================================================================
# R4: taller_bloquea_domicilio — si hay taller confirmado, no se puede domicilio
# =============================================================================

class TestTallerBloqueaDomicilio:
    """R4: taller confirmado impide domicilio ese día."""

    def test_fecha_sin_taller_no_bloquea_domicilio(self, app):
        with app.app_context():
            assert taller_bloquea_domicilio("2026-11-04") is False

    def test_fecha_con_un_taller_bloquea_domicilio(self, app):
        with app.app_context():
            db.session.add(Cita(
                cliente_nombre="Cliente 1",
                carro_descripcion="Carro 1",
                fallo="Fallo 1",
                modalidad="taller",
                direccion="",
                fecha="2026-11-04",
                estado="confirmada",
            ))
            db.session.commit()
            assert taller_bloquea_domicilio("2026-11-04") is True


# =============================================================================
# R11: campos_requeridos_para_confirmar
# =============================================================================

class TestCamposRequeridos:
    """R11: campos obligatorios para confirmar."""

    def test_todos_los_campos_presentes_no_faltan(self, app):
        datos = {
            "cliente_nombre": "Cliente",
            "carro_descripcion": "Carro",
            "fallo": "Fallo",
            "modalidad": "taller",
            "fecha": "2026-11-04",
        }
        assert campos_requeridos_para_confirmar(datos) == []

    def test_faltan_todos_los_campos(self, app):
        assert campos_requeridos_para_confirmar({}) == [
            "cliente_nombre",
            "carro_descripcion",
            "fallo",
            "modalidad",
            "fecha",
        ]

    def test_falta_solo_fecha(self, app):
        datos = {
            "cliente_nombre": "Cliente",
            "carro_descripcion": "Carro",
            "fallo": "Fallo",
            "modalidad": "taller",
        }
        assert campos_requeridos_para_confirmar(datos) == ["fecha"]

    def test_modalidad_vacia_se_considera_faltante(self, app):
        datos = {
            "cliente_nombre": "Cliente",
            "carro_descripcion": "Carro",
            "fallo": "Fallo",
            "modalidad": "",
            "fecha": "2026-11-04",
        }
        assert campos_requeridos_para_confirmar(datos) == ["modalidad"]


# =============================================================================
# R13: confirmar_con_capacidad_atomica
# =============================================================================

class TestConfirmarAtomica:
    """R13: confirmación atómica con comprobación de capacidad."""

    def test_confirma_cita_propuesta_con_espacio(self, app):
        with app.app_context():
            cita = Cita(
                cliente_nombre="Cliente",
                carro_descripcion="Carro",
                fallo="Fallo",
                modalidad="taller",
                direccion="",
                fecha="2026-11-04",
                estado="propuesta",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            ok, mensaje = confirmar_con_capacidad_atomica(cita)
            assert ok is True
            assert mensaje == ""
            assert cita.estado == "confirmada"

    def test_no_confirma_si_ya_esta_confirmada(self, app):
        with app.app_context():
            cita = Cita(
                cliente_nombre="Cliente",
                carro_descripcion="Carro",
                fallo="Fallo",
                modalidad="taller",
                direccion="",
                fecha="2026-11-04",
                estado="confirmada",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            ok, mensaje = confirmar_con_capacidad_atomica(cita)
            assert ok is False
            assert "propuesta" in mensaje

    def test_no_confirma_si_no_hay_espacio(self, app):
        with app.app_context():
            # Dos talleres ya confirmados
            db.session.add_all([
                Cita(
                    cliente_nombre="C1", carro_descripcion="Carro 1", fallo="Fallo 1",
                    modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
                ),
                Cita(
                    cliente_nombre="C2", carro_descripcion="Carro 2", fallo="Fallo 2",
                    modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
                ),
            ])
            db.session.commit()

            cita = Cita(
                cliente_nombre="C3", carro_descripcion="Carro 3", fallo="Fallo 3",
                modalidad="taller", direccion="", fecha="2026-11-04", estado="propuesta",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            ok, mensaje = confirmar_con_capacidad_atomica(cita)
            assert ok is False
            assert cita.estado == "propuesta"  # No cambió


# =============================================================================
# R8: validar_cambio_fecha
# =============================================================================

class TestValidarCambioFecha:
    """R8: cambio de fecha verifica capacidad del nuevo día."""

    def test_cambio_a_fecha_con_espacio_es_valido(self, app):
        with app.app_context():
            cita = Cita(
                cliente_nombre="Cliente", carro_descripcion="Carro", fallo="Fallo",
                modalidad="taller", direccion="", fecha="2026-11-05", estado="confirmada",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            ok, mensaje = validar_cambio_fecha("2026-11-05", "2026-11-04", "taller", cita_id_excluir=cita.id)
            assert ok is True
            assert mensaje == ""

    def test_cambio_a_fecha_llena_no_es_valido(self, app):
        with app.app_context():
            # Fecha destino ya tiene 2 talleres confirmados (día lleno)
            db.session.add_all([
                Cita(
                    cliente_nombre="C1", carro_descripcion="Carro 1", fallo="Fallo 1",
                    modalidad="taller", direccion="", fecha="2026-11-06", estado="confirmada",
                ),
                Cita(
                    cliente_nombre="C2", carro_descripcion="Carro 2", fallo="Fallo 2",
                    modalidad="taller", direccion="", fecha="2026-11-06", estado="confirmada",
                ),
            ])
            # Cita origen en otra fecha
            cita = Cita(
                cliente_nombre="C3", carro_descripcion="Carro 3", fallo="Fallo 3",
                modalidad="taller", direccion="", fecha="2026-11-05", estado="confirmada",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            ok, mensaje = validar_cambio_fecha("2026-11-05", "2026-11-06", "taller", cita_id_excluir=cita.id)
            assert ok is False
            assert "espacio" in mensaje.lower() or "complet" in mensaje.lower() or "lleno" in mensaje.lower()


# =============================================================================
# R9: liberar_capacidad / cancelar_cita
# =============================================================================

class TestLiberarCapacidad:
    """R9: cancelación conserva el registro y libera capacidad."""

    def test_cancelar_cita_cambia_estado_a_cancelada(self, app):
        with app.app_context():
            cita = Cita(
                cliente_nombre="Cliente", carro_descripcion="Carro", fallo="Fallo",
                modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
            )
            db.session.add(cita)
            db.session.commit()
            db.session.refresh(cita)

            liberar_capacidad(cita)
            assert cita.estado == "cancelada"

    def test_despues_de_cancelar_hay_espacio(self, app):
        with app.app_context():
            db.session.add_all([
                Cita(
                    cliente_nombre="C1", carro_descripcion="Carro 1", fallo="Fallo 1",
                    modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
                ),
                Cita(
                    cliente_nombre="C2", carro_descripcion="Carro 2", fallo="Fallo 2",
                    modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
                ),
            ])
            db.session.commit()

            cita = Cita.query.filter_by(fecha="2026-11-04", modalidad="taller").first()
            liberar_capacidad(cita)

            assert hay_espacio_taller("2026-11-04") is True
            assert Cita.query.filter_by(fecha="2026-11-04", estado="confirmada").count() == 1


# =============================================================================
# R14: datos_personales_no_a_ia (placeholder)
# =============================================================================

class TestDatosPersonalesNoAIa:
    """R14: datos_personales_no_a_ia es un placeholder que recuerda la regla.

    La limpieza real se hace en app.services.ia_service._limpiar_datos_personales
    antes de enviar al modelo de IA.
    """

    def test_placeholder_devuelve_texto_sin_cambios(self, app):
        texto = "El carro hace ruido al frenar"
        resultado = datos_personales_no_a_ia(texto)
        assert resultado == texto


# =============================================================================
# validar_confirmacion (combinación de reglas de capacidad R1-R4)
# =============================================================================

class TestValidarConfirmacion:
    """Pruebas de validar_confirmacion (R1-R4 combinadas)."""

    def test_taller_en_fecha_vacia_es_valido(self, app):
        with app.app_context():
            ok, mensaje = validar_confirmacion(
                {"modalidad": "taller", "fecha": "2026-11-04"}, fecha="2026-11-04"
            )
            assert ok is True
            assert mensaje == ""

    def test_domicilio_en_fecha_con_taller_no_es_valido(self, app):
        with app.app_context():
            db.session.add(Cita(
                cliente_nombre="C1", carro_descripcion="Carro 1", fallo="Fallo 1",
                modalidad="taller", direccion="", fecha="2026-11-04", estado="confirmada",
            ))
            db.session.commit()

            ok, mensaje = validar_confirmacion(
                {"modalidad": "domicilio", "fecha": "2026-11-04"}, fecha="2026-11-04"
            )
            assert ok is False
            assert "domicilio" in mensaje.lower() or "taller" in mensaje.lower()
