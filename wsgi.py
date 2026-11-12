"""Punto de entrada WSGI para despliegue en producción (Render, gunicorn).

Crea la aplicación Flask mediante la factoría create_app() y expone
la variable `app` que gunicorn busca por defecto.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe (desarrollo local)
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Solo para pruebas locales directas; en producción usa gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
