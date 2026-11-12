"""Configuración de pytest para la app CitasTaller.

Provee una aplicación Flask con base de datos SQLite temporal para cada prueba,
para que las pruebas sean aisladas y no toquen la base de datos real.
"""

import os
import tempfile

import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Crea una app de prueba con base de datos SQLite temporal."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    app = create_app()
    app.config["TESTING"] = True
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
    """Cliente de prueba de Flask."""
    return app.test_client()
