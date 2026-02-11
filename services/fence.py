from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from core.utils import ceil_div


id = "fence_install"
label = "Cerca elétrica (instalação)"


def render_fields():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        perimetro = st.number_input("Perímetro (m)", value=36.0, min_value=1.0, step=1.0, key="f_perimetro")
    with c2:
        fios = st.number_input("Qtd. fios", value=6, min_value=1, step=1, key="f_fios")
    with c3:
        espac = st.number_input("Espaçamento (m)", value=2.5, min_value=0.5, step=0.1, key="f_esp")
    with c4:
        cantos = st.number_input("Qtd. cantos", value=4, min_value=1, step=1, key="f_cantos")

    return {"perimetro": float(perimetro), "fios": int(fios), "espacamento": float(espac), "cantos": int(cantos)}


def _calc_hastes(perimetro: float, espacamento: float, cantos: int):
    vaos = ceil_div(perimetro, espacamento)
    total = vaos + 1
    retas = max(0, total - cantos)
    return retas, cantos


def compute(conn, inputs: dict):
    perimetro = float(inputs["perimetro"])
    fios = int(inputs["fios"])
    espac = float(inputs["espacamento"])
    cantos = int(inputs["cantos"])

    items = []
    subtotal = 0.0

    def add(desc, qty, unit):
        nonlocal subtotal
        sub = float(qty) * float(unit)
        items.append({"desc": desc, "qty": qty, "unit": float(unit), "sub": sub})
        subtotal += sub

    # Materiais
    hastes_retas, hastes_cantos = _calc_hastes(perimetro, espac, cantos)
    arame_m = perimetro * fios
    rolos_fio = ceil_div(arame_m, 200)

    add("Haste reta", hastes_retas, get_price(conn, "haste_reta"))
    add("Haste de canto", hastes_cantos, get_price(conn, "haste_canto"))
    add("Fio de aço (rolo 200m)", rolos_fio, get_price(conn, "fio_aco_200m"))
    add("Central SH1800", 1, get_price(conn, "central_sh1800"))
    add("Bateria", 1, get_price(conn, "bateria"))
    add("Sirene", 1, get_price(conn, "sirene"))

    add("Kit isoladores (100 un)", 1, get_price(conn, "kit_isoladores"))
    add("Cabo de alta isolação (50m)", 1, get_price(conn, "cabo_alta_50m"))
    add("Placas de aviso (kit)", 1, get_price(conn, "kit_placas"))
    add("Kit aterramento", 1, get_price(conn, "kit_aterramento"))

    # Mão de obra proporcional
    base = get_price(conn, "mao_cerca_base")
    por_m = get_price(conn, "mao_cerca_por_m")
    if base > 0:
        add("Mão de obra (taxa base)", 1, base)
    add("Mão de obra (R$/metro)", round(perimetro, 1), por_m)

    summary_full = (
        f"Instalação completa em {perimetro:.0f}m, com {fios} fios e hastes a cada {espac}m.\n"
        "Inclui central, bateria, sirene, aterramento, placas, testes e regulagem."
    )
    summary_client = (
        f"Cerca elétrica em {perimetro:.0f}m ({fios} fios).\n"
        "Inclui central, bateria, sirene, aterramento, placas e testes finais."
    )

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": f"{perimetro:.0f}m • {fios} fios",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


# plugin object
from services.registry import ServicePlugin
plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
