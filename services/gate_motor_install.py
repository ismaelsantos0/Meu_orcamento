from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl

id = "motor_install"
label = "Motor de portão (instalação)"


def render_fields():
    # Campo opcional só pra descrever melhor (não afeta cálculo)
    note = st.text_input("Observações (opcional)", value="", key="mi_note")
    return {"note": note}


def compute(conn, inputs: dict):
    mao = get_price(conn, "mao_motor_inst")

    items = [{"desc": "Instalação de motor de portão (mão de obra)", "qty": 1, "unit": float(mao), "sub": float(mao)}]
    subtotal = float(mao)

    note = (inputs.get("note") or "").strip()

    summary_full = "Instalação de motor de portão com configuração e testes."
    summary_client = "Instalação de motor de portão com testes."
    if note:
        summary_full += f"\nObs.: {note}"
        summary_client += f"\nObs.: {note}"

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": "Instalação",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


from services.registry import ServicePlugin
plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
