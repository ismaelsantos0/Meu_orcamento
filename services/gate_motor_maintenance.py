from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from services.base import ServicePlugin


id = "motor_maintenance"
label = "Motor de portão (manutenção)"


def render_fields():
    note = st.text_input("Observações (opcional)", value="", key="mm_note")
    return {"note": note}


def compute(conn, inputs: dict):
    mao = get_price(conn, "mao_motor_man")

    items = [{
        "desc": "Manutenção de motor de portão (mão de obra)",
        "qty": 1,
        "unit": float(mao),
        "sub": float(mao),
    }]
    subtotal = float(mao)

    note = (inputs.get("note") or "").strip()
    summary_full = "Manutenção do motor: diagnóstico, ajustes e testes."
    summary_client = "Manutenção do motor com ajustes e testes."
    if note:
        summary_full += f"\nObs.: {note}"
        summary_client += f"\nObs.: {note}"

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": "Manutenção",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
