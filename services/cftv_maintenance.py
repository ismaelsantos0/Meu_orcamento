from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl

id = "cftv_maintenance"
label = "Câmeras (manutenção)"


def render_fields():
    qtd = st.number_input("Câmeras com defeito", value=1, min_value=1, step=1, key="cm_qtd")
    return {"qtd_defeituosas": int(qtd)}


def compute(conn, inputs: dict):
    qtd = int(inputs["qtd_defeituosas"])

    items = []
    subtotal = 0.0

    def add(desc, qty, unit):
        nonlocal subtotal
        sub = float(qty) * float(unit)
        items.append({"desc": desc, "qty": qty, "unit": float(unit), "sub": sub})
        subtotal += sub

    add("Mão de obra (manutenção por câmera com defeito)", qtd, get_price(conn, "mao_cftv_por_camera_defeito"))

    summary_full = (
        f"Manutenção em {qtd} câmera(s) com defeito.\n"
        "Inclui diagnóstico, correções possíveis e testes de funcionamento."
    )
    summary_client = (
        f"Manutenção de {qtd} câmera(s) com defeito.\n"
        "Diagnóstico e testes."
    )

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": f"{qtd} câmera(s) com defeito",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


from services.registry import ServicePlugin
plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
