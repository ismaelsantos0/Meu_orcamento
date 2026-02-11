from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from services.base import ServicePlugin


id = "cftv_install"
label = "Câmeras (instalação)"


def render_fields():
    qtd = st.number_input("Quantidade de câmeras", value=4, min_value=1, step=1, key="ci_qtd")
    return {"qtd_cameras": int(qtd)}


def compute(conn, inputs: dict):
    qtd = int(inputs["qtd_cameras"])

    items = []
    subtotal = 0.0

    def add(desc, qty, unit):
        nonlocal subtotal
        sub = float(qty) * float(unit)
        items.append({"desc": desc, "qty": qty, "unit": float(unit), "sub": sub})
        subtotal += sub

    add("Mão de obra (instalação do DVR)", 1, get_price(conn, "mao_cftv_dvr"))
    add("Mão de obra (instalação por câmera)", qtd, get_price(conn, "mao_cftv_por_camera_inst"))

    summary_full = (
        f"Instalação de sistema CFTV com {qtd} câmera(s).\n"
        "Inclui instalação/configuração do DVR, organização e testes do sistema."
    )
    summary_client = (
        f"Instalação de CFTV ({qtd} câmera(s)) + DVR.\n"
        "Configuração e testes finais."
    )

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": f"{qtd} câmera(s) + DVR",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
