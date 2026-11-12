"""Script de cargado de fechas de prueba iniciales (seed).

Carga citas confirmadas para verificar las cifras de control C1-C4 de AGENTS.md:

- Lunes 16/11/2026: dos citas de taller confirmadas (C1, C4, C5, C6).
- Martes 17/11/2026: una visita a domicilio confirmada (C2, C3, C7).
- Miércoles 18/11/2026: sin citas (C4, C8).

Uso:
    uv run python app/data/seed.py
"""

from __future__ import annotations

from app import create_app, db
from app.models import Cita

ESTADO_CONFIRMADA = "confirmada"

CITAS_SEED = [
    {
        "cliente_nombre": "Cliente Prueba 1",
        "cliente_telefono": "2222-1111",
        "carro_descripcion": "Toyota Corolla 2015",
        "placa": "ABC-123",
        "fallo": "Ruido al frenar",
        "modalidad": "taller",
        "direccion": "San Jose, Centro",
        "fecha": "2026-11-16",  # Lunes
        "hora": "08:00",
        "estado": ESTADO_CONFIRMADA,
    },
    {
        "cliente_nombre": "Cliente Prueba 2",
        "cliente_telefono": "2222-2222",
        "carro_descripcion": "Hyundai Accent 2018",
        "placa": "DEF-456",
        "fallo": "Cambio de aceite",
        "modalidad": "taller",
        "direccion": "San Jose, Este",
        "fecha": "2026-11-16",  # Lunes
        "hora": "10:00",
        "estado": ESTADO_CONFIRMADA,
    },
    {
        "cliente_nombre": "Cliente Prueba 3",
        "cliente_telefono": "2222-3333",
        "carro_descripcion": "Nissan Sentra 2020",
        "placa": "GHI-789",
        "fallo": "Vibracion en direccion",
        "modalidad": "domicilio",
        "direccion": "San Pedro, Barrio Los Angeles, casa 123",
        "fecha": "2026-11-17",  # Martes
        "hora": "09:00",
        "estado": ESTADO_CONFIRMADA,
    },
]


def ejecutar_seed():
    """Inserta las citas de prueba si la tabla esta vacia."""
    app = create_app()
    with app.app_context():
        existe = db.session.query(Cita).first()
        if existe:
            print("Ya hay citas en la base de datos. Seed omitido (no se duplican).")
            return

        for datos in CITAS_SEED:
            cita = Cita(**datos)
            db.session.add(cita)

        db.session.commit()
        print(f"Seed completado: {len(CITAS_SEED)} citas de prueba insertadas.")
        print("- Lunes 2026-11-16: 2 citas de taller confirmadas.")
        print("- Martes 2026-11-17: 1 visita a domicilio confirmada.")
        print("- Miercoles 2026-11-18: sin citas.")


if __name__ == "__main__":
    ejecutar_seed()
