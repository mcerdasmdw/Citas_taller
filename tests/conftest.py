"""Configuración de pytest para la app CitasTaller.

Provee una aplicación Flask con base de datos SQLite temporal para cada prueba,
para que las pruebas sean aisladas y no toquen la base de datos real.

Las rutas ahora exigen sesión (login simple con credenciales de entorno), así
que el fixture `client` ya viene autenticado. El fixture `app` fija credenciales
de prueba ANTES de create_app para que .env no las pise (load_dotenv no
sobrescribe variables ya definidas).
"""

import os
import tempfile

import pytest
from app import create_app, db

# Credenciales de prueba para el login (se comparan con == en auth.py).
PRUEBA_USUARIO = "prueba@example.com"
PRUEBA_CLAVE = "clave-prueba-2026"


@pytest.fixture
def app():
    """Crea una app de prueba con base de datos SQLite temporal."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["APP_USUARIO"] = PRUEBA_USUARIO
    os.environ["APP_CLAVE"] = PRUEBA_CLAVE
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "clave-de-prueba"  # necesaria para la sesión de login
    with app.app_context():
        db.create_all()
    yield app
    # Cerrar sesiones y liberar el archivo antes de borrarlo (Windows lo bloquea si está abierto)
    try:
        db.session.remove()
    except Exception:
        pass
    try:
        db.engine.dispose()
    except Exception:
        pass
    try:
        os.close(db_fd)
    except OSError:
        pass
    try:
        os.unlink(db_path)
    except PermissionError:
        pass


@pytest.fixture
def client(app):
    """Cliente de prueba de Flask con sesión iniciada (las rutas exigen login)."""
    cliente = app.test_client()
    with cliente.session_transaction() as sess:
        sess["usuario"] = PRUEBA_USUARIO
    return cliente
