"""Servicio de agente de IA (capa de servicios).

El proveedor y modelo de IA están pendientes (AGENTS.md punto 14).
Mientras tanto, este servicio opera en modo simulado y respeta el contrato JSON
definido en el AGENTS.md. No envía datos personales (nombres, teléfonos, placas,
direcciones) al modelo.
"""

from __future__ import annotations

import re
from typing import Any


def _limpiar_datos_personales(texto: str) -> str:
    """Elimina patrones obvios de datos personales antes de enviar a la IA."""
    texto = re.sub(r"\+?\d[\d\s\-]{7,}", "[TELEFONO]", texto)
    texto = re.sub(r"[A-Z]{2,}\d{3,}[A-Z]?", "[PLACA]", texto)
    texto = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[FECHA]", texto)
    return texto


def preparar_propuesta(texto_solicitud: str, modalidad_indicada: str | None = None) -> dict[str, Any]:
    """Interpreta una solicitud y devuelve una propuesta en el contrato JSON.

    Modo simulado: no llama a proveedor externo. Extrae información básica
    usando heurística simple y devuelve exactamente las llaves del contrato.
    """
    texto_limpio = _limpiar_datos_personales(texto_solicitud)

    # Detección muy básica de carro (heurística, sin inventar)
    carro = "no indicado"
    patrones_carro = [
        r"(?:carro|vehículo|auto|automóvil|marca|modelo)[^\.\n]{0,60}",
    ]
    for patron in patrones_carro:
        m = re.search(patron, texto_limpio, re.IGNORECASE)
        if m:
            valor = m.group(0).strip()
            valor = re.sub(r"^(?:carro|vehículo|auto|automóvil|marca|modelo)\s*[:–-]?\s*", "", valor, flags=re.IGNORECASE)
            if len(valor) > 2:
                carro = valor[:80]
            break

    # Detección de fallo
    fallo = "no indicado"
    m_fallo = re.search(r"(?:falla|fallo|problema|ruido|no\s+[a-záéíóúñ]+)[^\.\n]{0,80}", texto_limpio, re.IGNORECASE)
    if m_fallo:
        fallo = m_fallo.group(0).strip()[:120]
    elif texto_limpio and texto_limpio != "[TELEFONO]":
        fallo = texto_limpio[:120]

    # Disponibilidad
    disponibilidad = "no indicado"
    m_disp = re.search(r"(?:mañana|pasado\s+mañana|lunes|martes|miércoles|jueves|viernes|sábado|domingo|hoy|\d{1,2}/\d{1,2})", texto_limpio, re.IGNORECASE)
    if m_disp:
        disponibilidad = m_disp.group(0).strip()

    # Modalidad
    modalidad = "no indicado"
    texto_lower = texto_limpio.lower()
    if "domicilio" in texto_lower:
        modalidad = "domicilio"
    elif "taller" in texto_lower:
        modalidad = "taller"
    elif modalidad_indicada:
        modalidad = modalidad_indicada

    # Fecha propuesta: solo si es inequívoca (formato AAAA-MM-DD)
    fecha_propuesta = "no indicado"
    m_fecha = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto_limpio)
    if m_fecha:
        fecha_propuesta = m_fecha.group(0)

    # Datos por aclarar
    datos_por_aclarar = []
    if carro == "no indicado":
        datos_por_aclarar.append("descripción del carro")
    if fallo == "no indicado":
        datos_por_aclarar.append("descripción del fallo")
    if disponibilidad == "no indicado":
        datos_por_aclarar.append("disponibilidad del cliente")
    if modalidad == "no indicado":
        datos_por_aclarar.append("modalidad (taller o domicilio)")
    if fecha_propuesta == "no indicado":
        datos_por_aclarar.append("fecha concreta")

    return {
        "carro": carro,
        "fallo": fallo,
        "disponibilidad_cliente": disponibilidad,
        "modalidad": modalidad,
        "fecha_propuesta": fecha_propuesta,
        "datos_por_aclarar": datos_por_aclarar,
    }


def validar_respuesta_ia(respuesta: dict) -> tuple[bool, str | None]:
    """Valida que la respuesta de la IA tenga la estructura del contrato.

    Retorna (valido, mensaje_error).
    """
    llaves_requeridas = {
        "carro",
        "fallo",
        "disponibilidad_cliente",
        "modalidad",
        "fecha_propuesta",
        "datos_por_aclarar",
    }

    if not isinstance(respuesta, dict):
        return False, "La respuesta no es un objeto JSON válido."

    faltantes = llaves_requeridas - set(respuesta.keys())
    if faltantes:
        return False, f"Faltan campos obligatorios: {', '.join(sorted(faltantes))}"

    if respuesta.get("modalidad") not in ("taller", "domicilio", "no indicado"):
        return False, "El campo 'modalidad' debe ser 'taller', 'domicilio' o 'no indicado'."

    if not isinstance(respuesta.get("datos_por_aclarar"), list):
        return False, "El campo 'datos_por_aclarar' debe ser un arreglo."

    return True, None
