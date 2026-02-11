import os
import sqlite3
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# =====================================================
# CONFIG
# =====================================================
APP_TITLE = "RR Smart Soluções — Gerador de Orçamentos"
EMPRESA = "RR Smart Soluções"
WHATSAPP = "97991728899"
GARANTIA_PADRAO = "6 meses"

DB_PATH = "data/db.sqlite"
LOGO_PATH = "assets/logo.png"


# =====================================================
# UTILS
# =====================================================
def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def ceil_div(a, b):
    return int((a + b - 1) // b)


# =====================================================
# DATABASE
# =====================================================
def db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            chave TEXT PRIMARY KEY,
            descricao TEXT,
            valor REAL
        )
    """)
    return conn


def set_preco(conn, chave, desc, valor):
    conn.execute("""
        INSERT INTO precos (chave, descricao, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET
        descricao=excluded.descricao,
        valor=excluded.valor
    """, (chave, desc, valor))
    conn.commit()


def get_preco(conn, chave, default=0.0):
    cur = conn.execute("SELECT valor FROM precos WHERE chave=?", (chave,))
    row = cur.fetchone()
    return float(row[0]) if row else default


def list_precos(conn):
    return conn.execute("SELECT chave, descricao, valor FROM precos ORDER BY chave").fetchall()


def add_item(itens, subtotal, conn, chave, qtd, desc):
    unit = get_preco(conn, chave)
    sub = unit * qtd
    itens.append((desc, qtd, unit, sub))
    return subtotal + sub


# =====================================================
# PDF — COMPLETO
# =====================================================
def gerar_pdf_completo(out, cliente, servico, resumo, itens, subtotal, desconto, total, pagamento, garantia):
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4

    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 110, width=70, height=70, mask="auto")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(130, h - 60, EMPRESA)
    c.setFont("Helvetica", 10)
    c.drawString(130, h - 80, f"WhatsApp: {WHATSAPP}")
    c.drawString(130, h - 95, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    y = h - 140
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Orçamento")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 15
    c.drawString(40, y, f"Serviço: {servico}")

    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "O que será entregue")
    y -= 15
    c.setFont("Helvetica", 10)
    for l in resumo.split("\n"):
        c.drawString(40, y, l)
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Descrição")
    c.drawString(300, y, "Qtd")
    c.drawString(360, y, "Unit")
    c.drawString(450, y, "Subtotal")
    y -= 5
    c.line(40, y, 550, y)
    y -= 15

    c.setFont("Helvetica", 9)
    for d, q, u, s in itens:
        c.drawString(40, y, d[:45])
        c.drawRightString(330, y, str(q))
        c.drawRightString(410, y, brl(u).replace("R$ ", ""))
        c.drawRightString(550, y, brl(s).replace("R$ ", ""))
        y -= 14

    y -= 10
    c.line(40, y, 550, y)
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(550, y, f"Subtotal: {brl(subtotal)}")
    if desconto > 0:
        y -= 15
        c.drawRightString(550, y, f"Desconto: - {brl(desconto)}")
    y -= 18
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"TOTAL: {brl(total)}")

    y -= 35
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Condições")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 14
    c.drawString(40, y, f"Garantia: {garantia}")
    y -= 14
    c.drawString(40, y, "Validade do orçamento: 7 dias")

    c.save()


# =====================================================
# PDF — RESUMIDO
# =====================================================
def gerar_pdf_resumido(out, cliente, servico, total, pagamento, garantia):
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4

    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 110, width=70, height=70, mask="auto")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(130, h - 60, EMPRESA)
    c.setFont("Helvetica", 10)
    c.drawString(130, h - 85, f"WhatsApp: {WHATSAPP}")
    c.drawString(130, h - 100, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    y = h - 160
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Orçamento (Resumo)")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 18
    c.drawString(40, y, f"Serviço: {servico}")

    y -= 45
    c.setFont("Helvetica-Bold", 28)
    c.drawString(40, y, "VALOR FINAL")
    y -= 35
    c.setFont("Helvetica-Bold", 34)
    c.drawString(40, y, brl(total))

    y -= 50
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 15
    c.drawString(40, y, f"Garantia: {garantia} | Validade: 7 dias")

    c.save()


# =====================================================
# APP
# =====================================================
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.title("🧾 Gerador de Orçamentos — RR Smart Soluções")

conn = db()

# Seed inicial
if not list_precos(conn):
    base = [
        ("haste_reta", "Haste reta", 19),
        ("haste_canto", "Haste de canto", 50),
        ("fio_aco_200m", "Fio de aço 200m", 80),
        ("central", "Central eletrificadora", 310),
        ("bateria", "Bateria", 83),
        ("sirene", "Sirene", 2),
        ("isoladores", "Kit isoladores", 19.9),
        ("cabo_alta", "Cabo alta isolação", 75),
        ("placas", "Placas de aviso", 19),
        ("aterramento", "Kit aterramento", 165),
        ("concertina_10m", "Concertina 30cm (10m)", 90),
        ("concertina_linear", "Concertina linear (20m)", 53),
        ("mao_cerca", "Mão de obra cerca", 900),
        ("mao_concertina", "Mão de obra concertina", 300),
        ("mao_linear", "Mão de obra concertina linear", 250),
    ]
    for k, d, v in base:
        set_preco(conn, k, d, v)

tipo_relatorio = st.radio(
    "Tipo de relatório",
    ["Completo (detalhado)", "Resumido (cliente)"],
    horizontal=True
)

cliente = st.text_input("Nome do cliente")
servico = st.selectbox("Serviço", [
    "Cerca elétrica",
    "Cerca elétrica + concertina",
    "Concertina linear eletrificada"
])

perimetro = st.number_input("Perímetro (m)", value=36.0)
desconto = st.number_input("Desconto (R$)", value=0.0)
pagamento = "50% de entrada e 50% após finalizar o serviço"

if st.button("Gerar orçamento"):
    itens = []
    subtotal = 0.0

    if servico != "Concertina linear eletrificada":
        fios = 6
        hastes = ceil_div(perimetro, 2.5) + 1
        subtotal = add_item(itens, subtotal, conn, "haste_reta", hastes - 4, "Haste reta")
        subtotal = add_item(itens, subtotal, conn, "haste_canto", 4, "Haste de canto")
        subtotal = add_item(itens, subtotal, conn, "fio_aco_200m", ceil_div(perimetro * fios, 200), "Fio de aço")
        subtotal = add_item(itens, subtotal, conn, "central", 1, "Central")
        subtotal = add_item(itens, subtotal, conn, "bateria", 1, "Bateria")
        subtotal = add_item(itens, subtotal, conn, "sirene", 1, "Sirene")
        subtotal = add_item(itens, subtotal, conn, "isoladores", 1, "Isoladores")
        subtotal = add_item(itens, subtotal, conn, "cabo_alta", 1, "Cabo alta isolação")
        subtotal = add_item(itens, subtotal, conn, "placas", 1, "Placas")
        subtotal = add_item(itens, subtotal, conn, "aterramento", 1, "Aterramento")
        subtotal = add_item(itens, subtotal, conn, "mao_cerca", 1, "Mão de obra")

        if servico == "Cerca elétrica + concertina":
            subtotal = add_item(itens, subtotal, conn, "concertina_10m", ceil_div(perimetro, 10), "Concertina")
            subtotal = add_item(itens, subtotal, conn, "mao_concertina", 1, "Mão de obra concertina")

        resumo = "Instalação completa do sistema de segurança no perímetro informado."

    else:
        subtotal = add_item(itens, subtotal, conn, "concertina_linear", ceil_div(perimetro, 20), "Concertina linear")
        subtotal = add_item(itens, subtotal, conn, "central", 1, "Central")
        subtotal = add_item(itens, subtotal, conn, "bateria", 1, "Bateria")
        subtotal = add_item(itens, subtotal, conn, "sirene", 1, "Sirene")
        subtotal = add_item(itens, subtotal, conn, "cabo_alta", 1, "Cabo alta isolação")
        subtotal = add_item(itens, subtotal, conn, "placas", 1, "Placas")
        subtotal = add_item(itens, subtotal, conn, "aterramento", 1, "Aterramento")
        subtotal = add_item(itens, subtotal, conn, "mao_linear", 1, "Mão de obra")
        resumo = "Instalação de concertina linear eletrificada com sistema de alarme."

    total = max(0, subtotal - desconto)

    os.makedirs("output", exist_ok=True)
    nome = f"orcamento_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out = os.path.join("output", nome)

    if tipo_relatorio.startswith("Resumido"):
        gerar_pdf_resumido(out, cliente, servico, total, pagamento, GARANTIA_PADRAO)
    else:
        gerar_pdf_completo(out, cliente, servico, resumo, itens, subtotal, desconto, total, pagamento, GARANTIA_PADRAO)

    with open(out, "rb") as f:
        st.download_button("Baixar PDF", f, file_name=nome)
