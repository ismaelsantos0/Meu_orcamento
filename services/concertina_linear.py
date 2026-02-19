from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from core.utils import ceil_div
from core.pdf.service_descriptions import get_service_description
from services.base import ServicePlugin


id = "concertina_linear"
label = "Concertina linear eletrificada (instalação)"


def render_fields():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        perimetro = st.number_input("Perímetro (m)", value=36.0, min_value=1.0)
    with c2:
        fios = st.number_input("Qtd. fios", value=6, min_value=1)
    with c3:
        espac = st.number_input("Espaçamento (m)", value=2.5, min_value=0.5)
    with c4:
        cantos = st.number_input("Qtd. cantos", value=4, min_value=1)

    return {
        "perimetro": float(perimetro),
        "fios": int(fios),
        "espacamento": float(espac),
        "cantos": int(cantos),
    }


def compute(conn, inputs: dict):
    perimetro = inputs["perimetro"]
    fios = inputs["fios"]
    espac = inputs["espacamento"]
    cantos = inputs["cantos"]

    items = []
    subtotal = 0.0

    def add(desc, qty, unit):
        nonlocal subtotal
        sub = qty * unit
        items.append({"desc": desc, "qty": qty, "unit": unit, "sub": sub})
        subtotal += sub

    # HASTES
    vaos = ceil_div(perimetro, espac)
    hastes_totais = vaos + 1
    hastes_canto = cantos
    hastes_retas = max(0, hastes_totais - hastes_canto)

    add("Haste reta", hastes_retas, get_price(conn, "haste_reta"))
    add("Haste de canto", hastes_canto, get_price(conn, "haste_canto"))

    # CONCERTINA
    metros = perimetro * fios
    rolos = ceil_div(metros, 20)
    add("Concertina linear (rolo 20m)", rolos, get_price(conn, "concertina_linear_20m"))

    # SISTEMA
    add("Central SH1800", 1, get_price(conn, "central_sh1800"))
    add("Bateria", 1, get_price(conn, "bateria"))
    add("Sirene", 1, get_price(conn, "sirene"))
    add("Cabo de alta isolação (50m)", 1, get_price(conn, "cabo_alta_50m"))
    add("Kit aterramento", 1, get_price(conn, "kit_aterramento"))
    add("Placas de aviso (kit)", 1, get_price(conn, "kit_placas"))

    # MÃO DE OBRA
    add("Mão de obra (taxa base)", 1, get_price(conn, "mao_linear_base"))
    add("Mão de obra (R$/metro)", perimetro, get_price(conn, "mao_linear_por_m"))

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "items": items,
        "subtotal": subtotal,
        "subtotal_brl": brl(subtotal),
        "service_description": get_service_description("concertina_linear"),
    }


plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
