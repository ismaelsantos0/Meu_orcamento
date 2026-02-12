from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from services.base import ServicePlugin


id = "cftv_install"
label = "Câmeras (instalação)"


def render_fields():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        qtd_cameras = st.number_input("Quantidade de câmeras", value=4, min_value=1, step=1, key="ci_qtd")
    with c2:
        metros_cabo = st.number_input("Metros de cabo (Cat5e)", value=100.0, min_value=0.0, step=10.0, key="ci_cabo")
    with c3:
        usar_suporte = st.checkbox("Incluir suporte por câmera?", value=False, key="ci_suporte")
    with c4:
        usar_caixa = st.checkbox("Incluir caixa hermética por câmera?", value=False, key="ci_caixa")

    st.caption("Dica: balun e conectores são calculados automaticamente por câmera (você pode ajustar na tabela de preços).")

    return {
        "qtd_cameras": int(qtd_cameras),
        "metros_cabo": float(metros_cabo),
        "usar_suporte": bool(usar_suporte),
        "usar_caixa": bool(usar_caixa),
    }


def compute(conn, inputs: dict):
    qtd = int(inputs["qtd_cameras"])
    metros_cabo = float(inputs["metros_cabo"])
    usar_suporte = bool(inputs["usar_suporte"])
    usar_caixa = bool(inputs["usar_caixa"])

    items = []
    subtotal = 0.0

    def add(desc, qty, unit):
        nonlocal subtotal
        qty = float(qty)
        unit = float(unit)
        sub = qty * unit
        items.append({"desc": desc, "qty": (int(qty) if qty.is_integer() else round(qty, 2)), "unit": unit, "sub": sub})
        subtotal += sub

    # =========================
    # MATERIAIS
    # =========================
    add("Câmera (un)", qtd, get_price(conn, "cftv_camera"))
    add("DVR (un)", 1, get_price(conn, "cftv_dvr"))
    add("HD para DVR (un)", 1, get_price(conn, "cftv_hd"))
    add("Fonte colmeia 12V 15A (un)", 1, get_price(conn, "cftv_fonte_colmeia"))

    # Cabos / acessórios
    add("Cabo U/UTP Cat5e (metro)", metros_cabo, get_price(conn, "cftv_cabo_cat5_m"))

    # Balun e conectores por câmera (padrão comum: 1 balun por câmera; 1 p4 macho + 1 p4 fêmea por câmera)
    add("Balun (un)", qtd, get_price(conn, "cftv_balun"))
    add("Conector P4 macho (un)", qtd, get_price(conn, "cftv_conector_p4_macho"))
    add("Conector P4 fêmea (un)", qtd, get_price(conn, "cftv_conector_p4_femea"))

    if usar_suporte:
        add("Suporte para câmera (un)", qtd, get_price(conn, "cftv_suporte_camera"))

    if usar_caixa:
        add("Caixa hermética / sobrepor (un)", qtd, get_price(conn, "cftv_caixa_hermetica"))

    # =========================
    # MÃO DE OBRA
    # =========================
    add("Mão de obra (instalação do DVR)", 1, get_price(conn, "mao_cftv_dvr"))
    add("Mão de obra (instalação por câmera)", qtd, get_price(conn, "mao_cftv_por_camera_inst"))

    summary_full = (
        f"Instalação de sistema CFTV com {qtd} câmera(s).\n"
        "Inclui materiais principais (câmeras, DVR, HD, fonte, acessórios), passagem/organização de cabos,\n"
        "instalação/configuração do DVR e testes finais do sistema."
    )
    summary_client = (
        f"Instalação de CFTV com {qtd} câmera(s) + DVR.\n"
        "Inclui configuração e testes finais."
    )

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": f"{qtd} câmera(s) • cabo: {metros_cabo:.0f}m",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)