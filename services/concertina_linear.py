from datetime import datetime
import streamlit as st

from core.db import get_price
from core.money import brl
from core.utils import ceil_div
from services.base import ServicePlugin


id = "concertina_linear_install"
label = "Concertina linear eletrificada (instalação)"


def render_fields():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        perimetro = st.number_input(
            "Perímetro (m)", value=36.0, min_value=1.0, step=1.0, key="cl_perimetro"
        )
    with c2:
        fios = st.number_input(
            "Qtd. fios", value=6, min_value=1, step=1, key="cl_fios"
        )
    with c3:
        espac = st.number_input(
            "Espaçamento (m)", value=2.5, min_value=0.5, step=0.1, key="cl_esp"
        )
    with c4:
        cantos = st.number_input(
            "Qtd. cantos", value=4, min_value=1, step=1, key="cl_cantos"
        )

    return {
        "perimetro": float(perimetro),
        "fios": int(fios),
        "espacamento": float(espac),
        "cantos": int(cantos),
    }


def _calc_hastes(perimetro: float, espacamento: float, cantos: int):
    """
    Calcula hastes pela lógica:
    vãos = ceil(perimetro/espacamento)
    hastes_totais = vãos + 1
    hastes_canto = cantos
    hastes_retas = hastes_totais - cantos (mínimo 0)
    """
    vaos = ceil_div(perimetro, espacamento)
    hastes_totais = vaos + 1
    hastes_canto = int(max(1, cantos))
    hastes_retas = max(0, int(hastes_totais) - hastes_canto)
    return hastes_retas, hastes_canto, int(hastes_totais), int(vaos)


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

    # =========================
    # ESTRUTURA (HASTES)
    # =========================
    hastes_retas, hastes_canto, hastes_totais, vaos = _calc_hastes(perimetro, espac, cantos)

    add("Haste reta", hastes_retas, get_price(conn, "haste_reta"))
    add("Haste de canto", hastes_canto, get_price(conn, "haste_canto"))

    # =========================
    # CONCERTINA LINEAR
    # =========================
    metros_linear = perimetro * fios
    rolos = ceil_div(metros_linear, 20)

    add(
        f"Concertina linear (rolo 20m) — {fios} fios ({metros_linear:.0f}m)",
        rolos,
        get_price(conn, "concertina_linear_20m"),
    )

    # =========================
    # SISTEMA (MANTÉM CENTRAL/SIRENE/BATERIA)
    # =========================
    add("Central SH1800", 1, get_price(conn, "central_sh1800"))
    add("Bateria", 1, get_price(conn, "bateria"))
    add("Sirene", 1, get_price(conn, "sirene"))
    add("Cabo de alta isolação (50m)", 1, get_price(conn, "cabo_alta_50m"))
    add("Kit aterramento", 1, get_price(conn, "kit_aterramento"))
    add("Placas de aviso (kit)", 1, get_price(conn, "kit_placas"))

    # =========================
    # MÃO DE OBRA (PROPORCIONAL AO PERÍMETRO)
    # =========================
    base = get_price(conn, "mao_linear_base")
    por_m = get_price(conn, "mao_linear_por_m")
    if base > 0:
        add("Mão de obra (taxa base)", 1, base)
    add("Mão de obra (R$/metro)", round(perimetro, 1), por_m)

    summary_full = (
        f"Instalação de concertina linear eletrificada em {perimetro:.0f}m, com {fios} fio(s) e hastes a cada {espac}m.\n"
        "A concertina linear realiza a eletrificação (sem fio de aço tradicional), mantendo central, bateria e sirene.\n"
        "Inclui estrutura com hastes (retas e cantos), aterramento, placas, testes e regulagem."
    )
    summary_client = (
        f"Concertina linear eletrificada em {perimetro:.0f}m ({fios} fio(s)), com hastes a cada {espac}m.\n"
        "Inclui central, bateria, sirene, aterramento, placas e testes finais."
    )

    return {
        "id": f"{datetime.now().timestamp()}",
        "service_id": id,
        "service_name": label,
        "service_hint": f"{perimetro:.0f}m • {fios} fio(s) • hastes: {hastes_totais} (esp. {espac}m)",
        "inputs": inputs,
        "items": items,
        "subtotal": float(subtotal),
        "subtotal_brl": brl(float(subtotal)),
        "summary_full": summary_full,
        "summary_client": summary_client,
    }


plugin = ServicePlugin(id=id, label=label, render_fields=render_fields, compute=compute)
