import os
import sqlite3
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# =========================================================
# CONFIG
# =========================================================
APP_TITLE = "RR Smart Soluções — Gerador de Orçamentos"
DB_PATH = "data/db.sqlite"
LOGO_PATH = "assets/logo.png"

EMPRESA = "RR Smart Soluções"
WHATSAPP = "97991728899"
GARANTIA_PADRAO = "6 meses"


# =========================================================
# DB
# =========================================================
def db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS precos (
            chave TEXT PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL
        )
        """
    )
    return conn


def get_preco(conn, chave, default=0.0):
    cur = conn.execute("SELECT valor FROM precos WHERE chave=?", (chave,))
    row = cur.fetchone()
    return float(row[0]) if row else float(default)


def set_preco(conn, chave, descricao, valor):
    conn.execute(
        """
        INSERT INTO precos (chave, descricao, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE
        SET descricao=excluded.descricao, valor=excluded.valor
        """,
        (chave, descricao, float(valor)),
    )
    conn.commit()


def list_precos(conn):
    cur = conn.execute("SELECT chave, descricao, valor FROM precos ORDER BY chave")
    return cur.fetchall()


# =========================================================
# PDF helpers
# =========================================================
def brl(v: float) -> str:
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


# =========================================================
# PDF COMPLETO
# =========================================================
def gerar_pdf_orcamento(
    out_path: str,
    cliente: str,
    servico: str,
    resumo_entrega: str,
    itens: list,  # [(desc, qtd, valor_unit, subtotal)]
    subtotal: float,
    desconto_label: str,
    desconto_valor: float,
    total: float,
    pagamento: str,
    garantia: str,
    validade_dias: int = 7,
):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Header
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 120, width=80, height=80, mask="auto")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, h - 70, EMPRESA)

    c.setFont("Helvetica", 10)
    c.drawString(140, h - 88, f"WhatsApp: {WHATSAPP}")
    c.drawString(140, h - 104, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    # Cliente
    y = h - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Orçamento")
    y -= 18

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 16
    c.drawString(40, y, f"Serviço: {servico}")

    # Entrega
    y -= 28
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "O que será entregue")
    y -= 16

    c.setFont("Helvetica", 10)
    for line in resumo_entrega.split("\n"):
        line = line.strip()
        if not line:
            continue
        c.drawString(40, y, line[:110])
        y -= 14

    # Itens
    y -= 8
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Composição (materiais / serviços)")
    y -= 14

    c.setFont("Helvetica-Bold", 9)
    c.drawString(40, y, "Descrição")
    c.drawString(300, y, "Qtd")
    c.drawString(350, y, "Unit")
    c.drawString(430, y, "Subtotal")
    y -= 10
    c.line(40, y, 550, y)
    y -= 14

    c.setFont("Helvetica", 9)
    for desc, qtd, unit, sub in itens:
        if y < 120:
            c.showPage()
            y = h - 70

            # Re-header simples na nova página
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Composição (continuação)")
            y -= 18

            c.setFont("Helvetica-Bold", 9)
            c.drawString(40, y, "Descrição")
            c.drawString(300, y, "Qtd")
            c.drawString(350, y, "Unit")
            c.drawString(430, y, "Subtotal")
            y -= 10
            c.line(40, y, 550, y)
            y -= 14
            c.setFont("Helvetica", 9)

        c.drawString(40, y, str(desc)[:45])
        c.drawRightString(330, y, f"{qtd}")
        c.drawRightString(410, y, brl(float(unit)).replace("R$ ", ""))
        c.drawRightString(550, y, brl(float(sub)).replace("R$ ", ""))
        y -= 14

    # Totais
    y -= 6
    c.line(40, y, 550, y)
    y -= 18

    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(550, y, f"Subtotal: {brl(subtotal)}")
    y -= 14

    if desconto_valor > 0:
        c.drawRightString(550, y, f"Desconto ({desconto_label}): - {brl(desconto_valor)}")
        y -= 14

    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"TOTAL: {brl(total)}")

    # Pagamento/garantia
    y -= 28
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Condições")
    y -= 16

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 14
    c.drawString(40, y, f"Garantia: {garantia}")
    y -= 14
    c.drawString(40, y, f"Validade do orçamento: {validade_dias} dias")

    c.save()


# =========================================================
# PDF RESUMIDO (pra enviar pro cliente)
# =========================================================
def gerar_pdf_resumido(
    out_path: str,
    cliente: str,
    servico: str,
    valor_total: float,
    pagamento: str,
    garantia: str,
    validade_dias: int = 7,
):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Header
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 120, width=80, height=80, mask="auto")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(140, h - 70, EMPRESA)

    c.setFont("Helvetica", 10)
    c.drawString(140, h - 90, f"WhatsApp: {WHATSAPP}")
    c.drawString(140, h - 105, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    # Corpo
    y = h - 170
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Orçamento (Resumo)")
    y -= 28

    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 18
    c.drawString(40, y, f"Serviço: {servico}")

    # Destaque do valor
    y -= 40
    c.setFont("Helvetica-Bold", 26)
    c.drawString(40, y, "VALOR FINAL")
    y -= 34
    c.setFont("Helvetica-Bold", 34)
    c.drawString(40, y, brl(valor_total))

    # Condições curtas
    y -= 55
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Condições")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 14
    c.drawString(40, y, f"Garantia: {garantia} | Validade: {validade_dias} dias")

    c.save()


# =========================================================
# ORÇAMENTO helpers (sem nonlocal)
# =========================================================
def add_item(itens, subtotal, conn, chave, qtd, label=None):
    unit = get_preco(conn, chave)
    desc = label or chave
    sub = unit * qtd
    itens.append((desc, qtd, unit, sub))
    return subtotal + sub


def ceil_div(a, b):
    return int((a + b - 1) // b)


def calc_hastes(perimetro, espacamento, cantos=4):
    # Ex.: 36/2.5=14.4 -> arredonda p/ cima -> 15 intervalos -> 16 hastes
    intervalos = int(perimetro / espacamento)
    if (perimetro / espacamento) > intervalos:
        intervalos += 1
    hastes_total = intervalos + 1

    hastes_canto = int(cantos)
    hastes_retas = max(0, hastes_total - hastes_canto)
    return hastes_total, hastes_retas, hastes_canto


# =========================================================
# APP
# =========================================================
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.title("🧾 Gerador de Orçamentos — RR Smart Soluções")

conn = db()
menu = st.sidebar.radio("Menu", ["Gerar orçamento", "Editar preços"])

# Seed inicial
if not list_precos(conn):
    seeds = [
        ("haste_reta", "Haste de cerca", 19.0),
        ("haste_canto", "Haste de canto", 50.0),
        ("fio_aco_200m", "Fio de aço 200m", 80.0),
        ("central_sh1800", "Central SH1800", 310.0),
        ("bateria", "Bateria", 83.0),
        ("sirene", "Sirene", 2.0),
        ("concertina_10m", "Concertina 30cm (10m)", 90.0),
        ("concertina_linear_20m", "Concertina linear (20m)", 53.0),
        ("kit_isoladores", "Kit isoladores (100 un)", 19.90),
        ("cabo_alta_50m", "Cabo alta isolação (50m)", 75.0),
        ("kit_placas", "Kit placas aviso", 19.0),
        ("kit_aterramento", "Kit aterramento", 165.0),
        ("mao_obra_cerca", "Mão de obra — cerca elétrica", 900.0),
        ("mao_obra_concertina", "Mão de obra — concertina", 300.0),
        ("mao_obra_concertina_linear", "Mão de obra — concertina linear", 250.0),
        ("mao_obra_cftv_inst", "Mão de obra — CFTV (instalação)", 0.0),
        ("mao_obra_cftv_man", "Mão de obra — CFTV (manutenção)", 0.0),
        ("mao_obra_motor_inst", "Mão de obra — Motor (instalação)", 0.0),
        ("mao_obra_motor_man", "Mão de obra — Motor (manutenção)", 0.0),
    ]
    for k, d, v in seeds:
        set_preco(conn, k, d, v)

if menu == "Editar preços":
    st.subheader("💲 Tabela de preços (editável)")
    rows = list_precos(conn)

    with st.form("form_precos"):
        st.caption("Altere valores e descrições. O gerador usa automaticamente.")
        updated = []
        for chave, desc, val in rows:
            c1, c2, c3 = st.columns([2, 6, 2])
            with c1:
                st.text_input("Chave", value=chave, key=f"k_{chave}", disabled=True)
            with c2:
                new_desc = st.text_input("Descrição", value=desc, key=f"d_{chave}")
            with c3:
                new_val = st.number_input(
                    "Valor (R$)", value=float(val), min_value=0.0, step=1.0, key=f"v_{chave}"
                )
            updated.append((chave, new_desc, new_val))

        if st.form_submit_button("Salvar alterações"):
            for chave, d, v in updated:
                set_preco(conn, chave, d, v)
            st.success("Preços atualizados!")

else:
    st.subheader("🧾 Gerar orçamento (PDF)")

    colA, colB = st.columns(2)
    with colA:
        cliente = st.text_input("Nome do cliente", placeholder="Ex.: Maria Silva")
        telefone = st.text_input("Telefone / WhatsApp (opcional)", placeholder="Ex.: 95 9xxxx-xxxx")
    with colB:
        tipo = st.selectbox(
            "Tipo de serviço",
            [
                "Cerca elétrica (instalação)",
                "Cerca elétrica + concertina (instalação)",
                "Concertina linear eletrificada (instalação)",
                "Cerca elétrica (manutenção)",
                "Câmeras (instalação)",
                "Câmeras (manutenção)",
                "Motor de portão (instalação)",
                "Motor de portão (manutenção)",
            ],
        )
        garantia = st.text_input("Garantia", value=GARANTIA_PADRAO)

    st.divider()

    # Mantém o design: só adiciona um radio simples
    tipo_relatorio = st.radio(
        "Tipo de relatório",
        ["Completo (com composição)", "Resumido (só serviço + valor)"],
        horizontal=True,
    )

    # Defaults
    perimetro = 36.0
    fios = 6
    espacamento = 2.5
    cantos = 4

    # Campos específicos
    if "Cerca" in tipo or "Concertina" in tipo:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            perimetro = st.number_input("Perímetro (m)", value=36.0, min_value=1.0, step=1.0)
        with c2:
            if tipo.startswith("Concertina linear"):
                st.number_input("Qtd. fios", value=0, disabled=True)
                fios = 0
            else:
                fios = st.number_input("Qtd. fios", value=6, min_value=1, step=1)
        with c3:
            espacamento = st.number_input("Espaçamento (m)", value=2.5, min_value=0.5, step=0.1)
        with c4:
            cantos = st.number_input("Qtd. cantos", value=4, min_value=1, step=1)

    desconto_tipo = st.selectbox("Desconto", ["Sem desconto", "%", "R$"])
    desconto_val = 0.0
    if desconto_tipo != "Sem desconto":
        desconto_val = st.number_input("Valor do desconto", value=0.0, min_value=0.0, step=10.0)

    pagamento = st.text_input(
        "Condição de pagamento",
        value="50% de entrada e 50% após finalizar o serviço",
    )

    if st.button("Gerar PDF"):
        if not cliente.strip():
            st.error("Informe o nome do cliente.")
            st.stop()

        itens = []
        subtotal = 0.0
        resumo = "Serviço conforme combinado."

        # =====================================================
        # CERCA ELÉTRICA (instalação)
        # =====================================================
        if tipo.startswith("Cerca elétrica") and "manutenção" not in tipo:
            _, hastes_retas, hastes_canto = calc_hastes(perimetro, espacamento, cantos=int(cantos))

            # Fio total
            arame_m = perimetro * fios
            rolos_fio = ceil_div(arame_m, 200)

            # Materiais base
            subtotal = add_item(itens, subtotal, conn, "haste_reta", hastes_retas, "Haste reta")
            subtotal = add_item(itens, subtotal, conn, "haste_canto", hastes_canto, "Haste de canto")
            subtotal = add_item(itens, subtotal, conn, "fio_aco_200m", rolos_fio, "Fio de aço (rolo 200m)")
            subtotal = add_item(itens, subtotal, conn, "central_sh1800", 1, "Central SH1800")
            subtotal = add_item(itens, subtotal, conn, "bateria", 1, "Bateria")
            subtotal = add_item(itens, subtotal, conn, "sirene", 1, "Sirene")

            # Complementos
            subtotal = add_item(itens, subtotal, conn, "kit_isoladores", 1, "Kit isoladores (100 un)")
            subtotal = add_item(itens, subtotal, conn, "cabo_alta_50m", 1, "Cabo de alta isolação (50m)")
            subtotal = add_item(itens, subtotal, conn, "kit_placas", 1, "Placas de aviso (kit)")
            subtotal = add_item(itens, subtotal, conn, "kit_aterramento", 1, "Kit aterramento")

            # Mão de obra
            mao = get_preco(conn, "mao_obra_cerca")
            itens.append(("Mão de obra (instalação)", 1, mao, mao))
            subtotal += mao

            # Concertina extra
            if "+ concertina" in tipo:
                rolos = ceil_div(perimetro, 10)
                subtotal = add_item(itens, subtotal, conn, "concertina_10m", rolos, "Concertina 30cm (rolo 10m)")

                mao2 = get_preco(conn, "mao_obra_concertina")
                itens.append(("Mão de obra (instalação concertina)", 1, mao2, mao2))
                subtotal += mao2

                resumo = (
                    f"Instalação completa em {perimetro:.0f}m de perímetro, com {fios} fios e hastes a cada {espacamento}m,\n"
                    "incluindo concertina, central, bateria, sirene, aterramento, placas, testes e regulagem."
                )
            else:
                resumo = (
                    f"Instalação completa em {perimetro:.0f}m de perímetro, com {fios} fios e hastes a cada {espacamento}m.\n"
                    "Sistema entregue funcionando, com central, bateria, sirene, aterramento, placas, testes e regulagem."
                )

        # =====================================================
        # CONCERTINA LINEAR ELETRIFICADA (substitui fios)
        # =====================================================
        elif tipo.startswith("Concertina linear eletrificada"):
            rolos = ceil_div(perimetro, 20)

            subtotal = add_item(itens, subtotal, conn, "concertina_linear_20m", rolos, "Concertina linear (rolo 20m)")
            subtotal = add_item(itens, subtotal, conn, "central_sh1800", 1, "Central SH1800")
            subtotal = add_item(itens, subtotal, conn, "bateria", 1, "Bateria")
            subtotal = add_item(itens, subtotal, conn, "sirene", 1, "Sirene")
            subtotal = add_item(itens, subtotal, conn, "cabo_alta_50m", 1, "Cabo de alta isolação (50m)")
            subtotal = add_item(itens, subtotal, conn, "kit_aterramento", 1, "Kit aterramento")
            subtotal = add_item(itens, subtotal, conn, "kit_placas", 1, "Placas de aviso (kit)")

            mao = get_preco(conn, "mao_obra_concertina_linear")
            itens.append(("Mão de obra (instalação)", 1, mao, mao))
            subtotal += mao

            resumo = (
                f"Instalação de concertina linear eletrificada em {perimetro:.0f}m de perímetro.\n"
                "A própria concertina faz a função de eletrificação (sem fios tradicionais), mantendo central, bateria,\n"
                "sirene e sistema de alarme, com aterramento, placas, testes e regulagem."
            )

        # =====================================================
        # MANUTENÇÃO CERCA (simples)
        # =====================================================
        elif tipo == "Cerca elétrica (manutenção)":
            mao = get_preco(conn, "mao_obra_cerca", default=300.0)
            itens.append(("Manutenção de cerca elétrica (diagnóstico, ajustes, testes)", 1, mao, mao))
            subtotal = mao
            resumo = (
                "Manutenção e revisão do sistema de cerca elétrica: diagnóstico, reaperto, ajustes, teste de energia,\n"
                "verificação de aterramento, checagem de sirene/central e correção de pontos críticos."
            )

        # =====================================================
        # OUTROS SERVIÇOS (só mão de obra)
        # =====================================================
        elif tipo == "Câmeras (instalação)":
            mao = get_preco(conn, "mao_obra_cftv_inst", default=0.0)
            itens.append(("Instalação de câmeras (mão de obra)", 1, mao, mao))
            subtotal = mao
            resumo = "Instalação de sistema de câmeras conforme definido, com testes e orientação de uso."

        elif tipo == "Câmeras (manutenção)":
            mao = get_preco(conn, "mao_obra_cftv_man", default=0.0)
            itens.append(("Manutenção de câmeras (mão de obra)", 1, mao, mao))
            subtotal = mao
            resumo = "Manutenção e ajustes no sistema de câmeras: revisão, testes e correções necessárias."

        elif tipo == "Motor de portão (instalação)":
            mao = get_preco(conn, "mao_obra_motor_inst", default=0.0)
            itens.append(("Instalação de motor de portão (mão de obra)", 1, mao, mao))
            subtotal = mao
            resumo = "Instalação de motor de portão com configuração e testes finais."

        elif tipo == "Motor de portão (manutenção)":
            mao = get_preco(conn, "mao_obra_motor_man", default=0.0)
            itens.append(("Manutenção de motor de portão (mão de obra)", 1, mao, mao))
            subtotal = mao
            resumo = "Manutenção do motor de portão: diagnóstico, ajustes e testes de funcionamento."

        # =====================================================
        # DESCONTO
        # =====================================================
        desconto_valor = 0.0
        desconto_label = "—"
        if desconto_tipo == "%":
            desconto_label = f"{desconto_val:.2f}%"
            desconto_valor = subtotal * (desconto_val / 100.0)
        elif desconto_tipo == "R$":
            desconto_label = "R$"
            desconto_valor = min(desconto_val, subtotal)

        total = max(0.0, subtotal - desconto_valor)

        # =====================================================
        # GERAÇÃO DO ARQUIVO (2 opções)
        # =====================================================
        os.makedirs("output", exist_ok=True)
        filename_base = f"orcamento_{cliente.strip().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cliente_fmt = cliente.strip()
        if telefone.strip():
            cliente_fmt = f"{cliente_fmt}  ({telefone.strip()})"

        if tipo_relatorio == "Resumido (só serviço + valor)":
            filename = f"{filename_base}_RESUMO.pdf"
            out = os.path.join("output", filename)

            gerar_pdf_resumido(
                out_path=out,
                cliente=cliente_fmt,
                servico=tipo,
                valor_total=total,
                pagamento=pagamento,
                garantia=garantia,
                validade_dias=7,
            )
        else:
            filename = f"{filename_base}_COMPLETO.pdf"
            out = os.path.join("output", filename)

            gerar_pdf_orcamento(
                out_path=out,
                cliente=cliente_fmt,
                servico=tipo,
                resumo_entrega=resumo,
                itens=itens,
                subtotal=subtotal,
                desconto_label=desconto_label,
                desconto_valor=desconto_valor,
                total=total,
                pagamento=pagamento,
                garantia=garantia,
                validade_dias=7,
            )

        st.success("PDF gerado!")
        with open(out, "rb") as f:
            st.download_button(
                "Baixar orçamento (PDF)",
                f,
                file_name=filename,
                mime="application/pdf",
            )
