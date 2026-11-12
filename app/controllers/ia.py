from __future__ import annotations

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from app.services.ia_service import preparar_propuesta, validar_respuesta_ia

bp = Blueprint("ia", __name__, url_prefix="/ia")


@bp.route("/preparar", methods=["POST"])
def preparar():
    """Prepara una propuesta de cita con el agente de IA.

    Recibe solo información autorizada (sin datos personales) y devuelve
    el contrato JSON. El usuario debe revisar y confirmar después.
    """
    texto = (request.form.get("texto_solicitud") or "").strip()
    modalidad_indicada = (request.form.get("modalidad") or "").strip() or None

    if not texto:
        flash("Ingrese la solicitud del cliente antes de preparar con IA.", "error")
        return redirect(url_for("citas.formulario_nueva"))

    propuesta = preparar_propuesta(texto, modalidad_indicada)
    valido, error = validar_respuesta_ia(propuesta)

    if not valido:
        flash(f"Respuesta de IA inválida: {error}", "error")
        return redirect(url_for("citas.formulario_nueva"))

    # Guardar propuesta en la sesión para que el usuario la revise antes de confirmar.
    # No se guarda el texto original de la solicitud (puede contener datos personales).
    session["propuesta_ia"] = propuesta

    flash("Propuesta de IA preparada. Revise los datos antes de confirmar.", "success")
    return redirect(url_for("citas.formulario_nueva", _anchor="propuesta"))


@bp.route("/propuesta")
def ver_propuesta():
    """Muestra la última propuesta de IA generada (solo lectura)."""
    propuesta = session.get("propuesta_ia")
    if not propuesta:
        flash("No hay una propuesta de IA pendiente.", "info")
        return redirect(url_for("citas.formulario_nueva"))
    return render_template("propuesta_ia.html", propuesta=propuesta)


@bp.route("/api/preparar", methods=["POST"])
def api_preparar():
    """Endpoint JSON del agente de IA (para integración futura)."""
    datos = request.get_json(silent=True) or {}
    texto = datos.get("texto_solicitud", "")
    modalidad_indicada = datos.get("modalidad")

    if not texto:
        return jsonify({"error": "texto_solicitud requerido"}), 400

    propuesta = preparar_propuesta(texto, modalidad_indicada)
    valido, error = validar_respuesta_ia(propuesta)

    if not valido:
        return jsonify({"error": error, "propuesta": propuesta}), 422

    return jsonify(propuesta)
