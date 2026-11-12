"""Modelos de datos de la aplicación (capa Modelo del MVC)."""

from datetime import datetime
from app import db


class Cita(db.Model):
    """Modelo de cita de revisión de carro.

    Estados permitidos: propuesta, confirmada, cancelada, pendiente,
    en_proceso, completada, no_asistio.
    Solo las citas con estado 'confirmada' consumen capacidad.
    """

    __tablename__ = "citas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_nombre = db.Column(db.String(120), nullable=True)
    cliente_telefono = db.Column(db.String(40), nullable=True)
    carro_descripcion = db.Column(db.String(200), nullable=False)
    placa = db.Column(db.String(20), nullable=True)
    fallo = db.Column(db.Text, nullable=False)
    modalidad = db.Column(db.String(20), nullable=False)  # taller | domicilio
    direccion = db.Column(db.String(200), nullable=False, default="")
    fecha = db.Column(db.String(10), nullable=False)  # AAAA-MM-DD
    hora = db.Column(db.String(5), nullable=True)     # HH:MM opcional
    estado = db.Column(db.String(20), nullable=False, default="propuesta")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "cliente_nombre": self.cliente_nombre,
            "cliente_telefono": self.cliente_telefono,
            "carro_descripcion": self.carro_descripcion,
            "placa": self.placa,
            "fallo": self.fallo,
            "modalidad": self.modalidad,
            "direccion": self.direccion,
            "fecha": self.fecha,
            "hora": self.hora,
            "estado": self.estado,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
            "actualizado_en": self.actualizado_en.isoformat() if self.actualizado_en else None,
        }

    def __repr__(self):
        return f"<Cita {self.id} {self.fecha} {self.modalidad} {self.estado}>"
