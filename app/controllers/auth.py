"""Autenticación simple por usuario/contraseña de variables de entorno.

Regla de acceso (vive en este controlador): toda ruta de la app exige
sesión iniciada, excepto /login y los archivos estáticos. No usa base de
datos: las credenciales se leen de APP_USUARIO y APP_CLAVE del entorno
(.env, cargado en create_app) y se comparan con `==`. Si faltan esas
variables, /login no abre la app: se trata como credenciales imposibles
de cumplir y muestra el error normal del formulario.
"""

from __future__ import annotations

import os

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

bp = Blueprint("auth", __name__)

# Puntos de ruta accesibles sin sesión: el login y los archivos estáticos.
RUTAS_PUBLICAS = {"auth.login", "static"}

# Mensaje exacto que se muestra cuando las credenciales no sirven.
MENSAJE_ERROR_LOGIN = "Usuario o contraseña incorrectos"


@bp.before_app_request
def exigir_sesion():
    """Regla de acceso global: sin sesión, cualquier ruta (salvo /login y
    estáticos) redirige a /login. Cubre citas, ia y rutas /api/....

    Entrada: petición cualquiera. Salida: None si hay sesión o la ruta es
    pública; redirect a /login en caso contrario.
    """
    if request.endpoint is None or request.endpoint in RUTAS_PUBLICAS:
        return None
    if not session.get("usuario"):
        return redirect(url_for("auth.login"))
    return None


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Muestra y procesa el formulario de acceso.

    Entrada (POST): usuario (email) y clave del formulario. Salida: si
    coinciden con APP_USUARIO/APP_CLAVE del entorno, guarda
    session["usuario"] y redirige a / (calendario); si no, vuelve al
    formulario con el error "Usuario o contraseña incorrectos".
    """
    if request.method == "POST":
        usuario = (request.form.get("usuario") or "").strip()
        clave = request.form.get("clave") or ""

        usuario_env = os.environ.get("APP_USUARIO")
        clave_env = os.environ.get("APP_CLAVE")

        # Sin credenciales configuradas, el login es imposible de cumplir:
        # se muestra el error normal y la app sigue cerrada.
        if (
            usuario_env
            and clave_env
            and usuario == usuario_env
            and clave == clave_env
        ):
            session["usuario"] = usuario
            return redirect(url_for("citas.calendario"))

        flash(MENSAJE_ERROR_LOGIN, "error")

    return render_template("login.html")


@bp.route("/salir", methods=["POST"])
def salir():
    """Cierra la sesión y redirige a /login.

    Entrada: POST con sesión activa. Salida: sesión limpia, redirect a
    /login.
    """
    session.clear()
    return redirect(url_for("auth.login"))
