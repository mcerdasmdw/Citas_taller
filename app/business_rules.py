"""Reglas de negocio (capa de reglas, sin IA).

Todas las comprobaciones R1–R14 del AGENTS.md residen aquí.
"""

from datetime import time
from app import db
from app.models import Cita

# ---- Constantes ----
HORARIO_INICIO = time(7, 0)   # 07:00
HORARIO_FIN = time(16, 0)     # 16:00
MAX_TALLER_POR_DIA = 2
MAX_DOMICILIO_POR_DIA = 1


def _citas_confirmadas_por_fecha(fecha: str):
    """Devuelve las citas confirmadas de una fecha."""
    return Cita.query.filter_by(fecha=fecha, estado="confirmada").all()


def _contar_taller_confirmado(fecha: str) -> int:
    return sum(
        1 for c in _citas_confirmadas_por_fecha(fecha) if c.modalidad == "taller"
    )


def _contar_domicilio_confirmado(fecha: str) -> int:
    return sum(
        1 for c in _citas_confirmadas_por_fecha(fecha) if c.modalidad == "domicilio"
    )


def hay_espacio_taller(fecha: str) -> bool:
    """R1: Una fecha admite como máximo dos citas confirmadas de taller."""
    return _contar_taller_confirmado(fecha) < MAX_TALLER_POR_DIA


def hay_espacio_domicilio(fecha: str) -> bool:
    """R2: Una fecha admite como máximo una cita confirmada a domicilio."""
    return _contar_domicilio_confirmado(fecha) < MAX_DOMICILIO_POR_DIA


def domicilio_bloquea_dia(fecha: str) -> bool:
    """R3: Una visita a domicilio confirmada impide cualquier otra cita ese día."""
    return _contar_domicilio_confirmado(fecha) >= MAX_DOMICILIO_POR_DIA


def taller_bloquea_domicilio(fecha: str) -> bool:
    """R4: Si hay 1 o 2 talleres confirmados, no se puede confirmar domicilio ese día."""
    return _contar_taller_confirmado(fecha) >= 1


def hora_valida(hora_str: str | None) -> bool:
    """R5: La hora debe estar entre 07:00 y 16:00 si se registra."""
    if not hora_str:
        return True
    try:
        partes = hora_str.split(":")
        h = int(partes[0])
        m = int(partes[1]) if len(partes) > 1 else 0
        t = time(h, m)
        return HORARIO_INICIO <= t <= HORARIO_FIN
    except (ValueError, IndexError):
        return False


def campos_requeridos_para_confirmar(datos: dict) -> list[str]:
    """R11: Para confirmar se requieren cliente, carro, fallo, modalidad y fecha."""
    faltantes = []
    if not datos.get("cliente_nombre"):
        faltantes.append("cliente_nombre")
    if not datos.get("carro_descripcion"):
        faltantes.append("carro_descripcion")
    if not datos.get("fallo"):
        faltantes.append("fallo")
    if not datos.get("modalidad"):
        faltantes.append("modalidad")
    if not datos.get("fecha"):
        faltantes.append("fecha")
    return faltantes


def validar_confirmacion(datos: dict, fecha: str | None = None, cita_id_excluir: int | None = None) -> tuple[bool, str]:
    """Valida reglas de capacidad antes de confirmar o cambiar fecha.

    Retorna (valido, mensaje_error).
    """
    fecha = fecha or datos.get("fecha")
    modalidad = datos.get("modalidad")

    if not fecha:
        return False, "Fecha requerida."

    if modalidad == "taller":
        if not hay_espacio_taller(fecha):
            return False, "No hay espacio de taller disponible para esa fecha (máximo 2 carros)."
        if domicilio_bloquea_dia(fecha):
            return False, "No se puede confirmar taller: ya hay una visita a domicilio confirmada ese día."

    if modalidad == "domicilio":
        if not hay_espacio_domicilio(fecha):
            return False, "No hay espacio para visita a domicilio ese fecha (máximo 1 visita)."
        if taller_bloquea_domicilio(fecha):
            return False, "No se puede confirmar domicilio: ya hay citas de taller confirmadas ese día."

    return True, ""


def liberar_capacidad(cita: Cita):
    """R9: Cancelar conserva el registro y libera su capacidad (cambia estado a cancelada)."""
    cita.estado = "cancelada"
    db.session.add(cita)
    db.session.commit()


def propuesta_no_consume_capacidad():
    """R10: Las propuestas sin confirmar no consumen capacidad."""
    pass  # Nada que hacer: las citas en estado 'propuesta' no cuentan.


def datos_personales_no_a_ia(texto: str) -> str:
    """R14: placeholder para recordar que nombres, teléfonos, placas y direcciones
    no se envían a la IA. La limpieza real se hace antes de llamar al servicio de IA."""
    return texto


def requiere_accion_expresa_usuario() -> bool:
    """R6: Ninguna propuesta de la IA se confirmará sin una acción expresa del usuario.

    Entrada: ninguna
    Salida: True (el código siempre exige acción del usuario para confirmar)
    """
    return True


def validar_capacidad_antes_confirmar(fecha: str, modalidad: str) -> tuple[bool, str]:
    """R7: Antes de confirmar una cita, el código vuelve a consultar la capacidad de la fecha elegida.

    Entrada: fecha (AAAA-MM-DD), modalidad (taller|domicilio)
    Salida: (True, "") si hay espacio, (False, mensaje) si no
    """
    if modalidad == "taller":
        if not hay_espacio_taller(fecha):
            return False, "No hay espacio de taller disponible para esa fecha (máximo 2 carros)."
        if domicilio_bloquea_dia(fecha):
            return False, "No se puede confirmar taller: ya hay una visita a domicilio confirmada ese día."

    if modalidad == "domicilio":
        if not hay_espacio_domicilio(fecha):
            return False, "No hay espacio para visita a domicilio esa fecha (máximo 1 visita)."
        if taller_bloquea_domicilio(fecha):
            return False, "No se puede confirmar domicilio: ya hay citas de taller confirmadas ese día."

    return True, ""


def validar_cambio_fecha(
    fecha_original: str,
    fecha_nueva: str,
    modalidad: str,
    cita_id_excluir: int | None = None,
) -> tuple[bool, str]:
    """R8: Un cambio de fecha deberá comprobar la capacidad del nuevo día antes de guardar.

    Entrada: fecha original, fecha nueva, modalidad, id de cita a excluir (para no contar la cita que se mueve)
    Salida: (True, "") si se puede cambiar, (False, mensaje) si no hay espacio
    """
    if modalidad == "taller":
        query = Cita.query.filter_by(
            fecha=fecha_nueva, estado="confirmada", modalidad="taller"
        )
        if cita_id_excluir is not None:
            query = query.filter(Cita.id != cita_id_excluir)
        if query.count() >= MAX_TALLER_POR_DIA:
            return False, "No hay espacio de taller disponible en la fecha nueva (máximo 2 carros)."
        if domicilio_bloquea_dia(fecha_nueva):
            return False, "No se puede cambiar a taller: ya hay una visita a domicilio confirmada ese día."

    if modalidad == "domicilio":
        query = Cita.query.filter_by(
            fecha=fecha_nueva, estado="confirmada", modalidad="domicilio"
        )
        if cita_id_excluir is not None:
            query = query.filter(Cita.id != cita_id_excluir)
        if query.count() >= MAX_DOMICILIO_POR_DIA:
            return False, "No hay espacio para visita a domicilio en la fecha nueva (máximo 1 visita)."
        query_taller = Cita.query.filter_by(
            fecha=fecha_nueva, estado="confirmada", modalidad="taller"
        )
        if cita_id_excluir is not None:
            query_taller = query_taller.filter(Cita.id != cita_id_excluir)
        if query_taller.count() >= 1:
            return False, "No se puede cambiar a domicilio: ya hay citas de taller confirmadas ese día."

    return True, ""


def cancelar_cita(cita: Cita) -> None:
    """R9: Una cancelación conservará el registro de la cita y liberará su capacidad.

    Entrada: objeto Cita
    Salida: cambia estado a "cancelada" y guarda en BD
    """
    cita.estado = "cancelada"
    db.session.add(cita)
    db.session.commit()


def confirmar_con_capacidad_atomica(cita: Cita) -> tuple[bool, str]:
    """R13: La confirmación y su comprobación de capacidad se guardarán como una sola operación.

    Entrada: objeto Cita en estado "propuesta"
    Salida: (True, "") si se confirmó y guardó, (False, mensaje) si no hay espacio
    """
    if cita.estado != "propuesta":
        return False, "Solo se pueden confirmar citas en estado 'propuesta'."

    ok, mensaje = validar_capacidad_antes_confirmar(cita.fecha, cita.modalidad)
    if not ok:
        return False, mensaje

    cita.estado = "confirmada"
    db.session.add(cita)
    db.session.commit()

    return True, ""
