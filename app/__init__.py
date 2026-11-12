"""Factory de la aplicación Flask (patrón MVC)."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Cargar variables de entorno desde .env ANTES de configurar la BD
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    # Asegurar carpeta de instancia ANTES de cualquier operación de BD
    os.makedirs(app.instance_path, exist_ok=True)

    # Construir ruta absoluta a la base de datos SQLite
    db_path = os.path.join(app.instance_path, "citas.db")
    db_uri = os.environ.get("DATABASE_URL", "sqlite:///" + db_path)

    # Si DATABASE_URL apunta a un archivo SQLite, asegurar que exista su carpeta
    # (Render usa rutas relativas a instance/ o rutas absolutas a un disco montado)
    if db_uri.startswith("sqlite:///"):
        raw = db_uri[len("sqlite:///"):].replace("\\", "/")
        if raw and not raw.startswith(":memory:"):
            full = raw if (raw.startswith("/") or os.path.isabs(raw)) else os.path.join(app.instance_path, raw)
            parent = os.path.dirname(full)
            if parent:
                os.makedirs(parent, exist_ok=True)

    # Configuración base
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Inicializar extensiones
    db.init_app(app)

    # Registrar modelos y crear tablas
    from app import models  # noqa: F401
    with app.app_context():
        db.create_all()

    # Registrar controladores (rutas)
    from app.controllers import citas as citas_controller
    from app.controllers import ia as ia_controller
    app.register_blueprint(citas_controller.bp)
    app.register_blueprint(ia_controller.bp)

    return app
