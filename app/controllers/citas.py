from __future__ import annotations

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import Cita
from app.business_rules import (
    hora_valida,
    campos_requeridos_para_confirmar,
    confirmar_con_capacidad_atomica,
    validar_cambio_fecha,
    liberar_capacidad,
)

bp = Blueprint("citas", __name__, url_prefix="/")


# ---------------------------------------------------------------------------
# Rutas principales
# ---------------------------------------------------------------------------

@bp.route("/")
def calendario():
    """Muestra el calendario con citas confirmadas y disponibilidad por día."""
    citas = Cita.query.order_by(Cita.fecha, Cita.hora).all()
    return render_template("calendario.html", citas=citas)


@bp.route("/citas/nueva", methods=["GET"])
def formulario_nueva():
    """Abre el formulario de nueva cita."""
    return render_template("formulario_cita.html", cita=None, accion="nueva")


@bp.route("/citas", methods=["POST"])
def crear_cita():
    """Crea una cita en estado 'propuesta' (no consume capacidad aún)."""
    datos = request.form if request.form else request.get_json(silent=True) or {}

    carro = (datos.get("carro_descripcion") or "").strip()
    fallo = (datos.get("fallo") or "").strip()
    modalidad = (datos.get("modalidad") or "").strip()
    fecha = (datos.get("fecha") or "").strip()
    hora = (datos.get("hora") or "").strip() or None
    cliente_nombre = (datos.get("cliente_nombre") or "").strip() or None
    cliente_telefono = (datos.get("cliente_telefono") or "").strip() or None
    placa = (datos.get("placa") or "").strip() or None
    direccion = (datos.get("direccion") or "").strip()

    if not fallo:
        flash("La descripción del fallo es obligatoria.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    if modalidad not in ("taller", "domicilio"):
        flash("Debe seleccionar una modalidad: Taller o Domicilio.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    if not fecha:
        flash("La fecha es obligatoria.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    # Dirección obligatoria para visitas a domicilio.
    if modalidad == "domicilio" and not direccion:
        flash("La dirección es obligatoria para visitas a domicilio.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    if hora and not hora_valida(hora):
        flash("La hora debe estar entre 07:00 y 16:00.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    cita = Cita(
        cliente_nombre=cliente_nombre,
        cliente_telefono=cliente_telefono,
        carro_descripcion=carro or "no indicado",
        placa=placa,
        fallo=fallo,
        modalidad=modalidad,
        direccion=direccion,
        fecha=fecha,
        hora=hora,
        estado="propuesta",
    )
    db.session.add(cita)
    db.session.commit()

    flash("Cita creada como propuesta (sin reservar espacio aún).", "success")
    return redirect(url_for("citas.detalle_cita", cita_id=cita.id))


@bp.route("/citas/<int:cita_id>")
def detalle_cita(cita_id: int):
    """Muestra el detalle de una cita."""
    cita = Cita.query.get_or_404(cita_id)
    return render_template("detalle_cita.html", cita=cita)


@bp.route("/citas/<int:cita_id>/confirmar", methods=["POST"])
def confirmar_cita(cita_id: int):
    """Confirma una cita tras validar capacidad (R7 y R13)."""
    cita = Cita.query.get_or_404(cita_id)

    if cita.estado == "confirmada":
        flash("La cita ya está confirmada.", "info")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    datos = {
        "cliente_nombre": cita.cliente_nombre,
        "carro_descripcion": cita.carro_descripcion,
        "fallo": cita.fallo,
        "modalidad": cita.modalidad,
        "fecha": cita.fecha,
    }

    # R11: campos requeridos
    faltantes = campos_requeridos_para_confirmar(datos)
    if faltantes:
        flash(f"Faltan campos obligatorios para confirmar: {', '.join(faltantes)}", "error")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    # R7 + R13: re-consulta capacidad y confirma en una sola operación atómica.
    ok, mensaje = confirmar_con_capacidad_atomica(cita)
    if not ok:
        flash(mensaje, "error")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    flash("Cita confirmada correctamente.", "success")
    return redirect(url_for("citas.detalle_cita", cita_id=cita.id))


@bp.route("/citas/<int:cita_id>/cambiar-fecha", methods=["POST"])
def cambiar_fecha(cita_id: int):
    """Cambia la fecha de una cita tras comprobar capacidad del nuevo día (R8)."""
    cita = Cita.query.get_or_404(cita_id)
    nueva_fecha = (request.form.get("fecha") or "").strip()
    nueva_hora = (request.form.get("hora") or "").strip() or None

    if not nueva_fecha:
        flash("La nueva fecha es obligatoria.", "error")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    if nueva_hora and not hora_valida(nueva_hora):
        flash("La hora debe estar entre 07:00 y 16:00.", "error")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    # R8: comprobar capacidad del nuevo día antes de guardar (excluyendo esta cita).
    valido, mensaje = validar_cambio_fecha(
        cita.fecha, nueva_fecha, cita.modalidad, cita_id_excluir=cita.id
    )
    if not valido:
        flash(mensaje, "error")
        return redirect(url_for("citas.detalle_cita", cita_id=cita.id))

    cita.fecha = nueva_fecha
    cita.hora = nueva_hora
    db.session.add(cita)
    db.session.commit()

    flash("Fecha de la cita actualizada.", "success")
    return redirect(url_for("citas.detalle_cita", cita_id=cita.id))


@bp.route("/citas/<int:cita_id>/cancelar", methods=["POST"])
def cancelar_cita(cita_id: int):
    """Cancela una cita: conserva el registro y libera capacidad (R9)."""
    cita = Cita.query.get_or_404(cita_id)
    liberar_capacidad(cita)
    flash("Cita cancelada. El registro se conserva y se liberó su capacidad.", "info")
    return redirect(url_for("citas.calendario"))


@bp.route("/citas/lista")
def lista_citas():
    """Lista todas las citas."""
    citas = Cita.query.order_by(Cita.fecha.desc(), Cita.hora).all()
    return render_template("lista_citas.html", citas=citas)


# ---------------------------------------------------------------------------
# API auxiliar para disponibilidad
# ---------------------------------------------------------------------------

@bp.route("/api/disponibilidad/<fecha>")
def api_disponibilidad(fecha: str):
    """Devuelve la disponibilidad de una fecha para el calendario."""
    citas_confirmadas = Cita.query.filter_by(fecha=fecha, estado="confirmada").all()
    talleres = sum(1 for c in citas_confirmadas if c.modalidad == "taller")
    domicilios = sum(1 for c in citas_confirmadas if c.modalidad == "domicilio")

    if domicilios >= 1:
        disponible = {"taller": 0, "domicilio": 0, "mensaje": "Día completo (visita a domicilio)."}
    elif talleres >= 2:
        disponible = {"taller": 0, "domicilio": 0, "mensaje": "Día completo (2 carros de taller)."}
    elif talleres == 1:
        disponible = {"taller": 1, "domicilio": 0, "mensaje": "Queda 1 espacio de taller; no disponible domicilio."}
    else:
        disponible = {"taller": 2, "domicilio": 1, "mensaje": "Día disponible: 2 talleres o 1 domicilio."}

    return jsonify({"fecha": fecha, "disponible": disponible})
