import os
import sqlite3
from datetime import datetime

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# =========================================================
# CONFIGURAÇÕES GERAIS
# =========================================================
APP_TITLE = "RR Smart Soluções — Gerador de Orçamentos"
DB_PATH = "data/db.sqlite"
LOGO_PATH = "assets/logo.png"

EMPRESA = "RR Smart Soluções"
WHATSAPP = "97991728899"
GARANTIA_PADRAO = "6 meses"
VALIDADE_PADRAO = 7


# =========================================================
# BANCO DE DADOS
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
    return conn.execute(
        "SELECT chave, descricao, valor FROM precos ORDER BY chave"
    ).fetchall()


def ensure_seed(conn):
    seeds = [
        ("haste_reta", "Haste de cerca", 19.0),
        ("haste_canto", "Haste de canto", 50.0),
        ("fio_aco_200m", "Fio de aço 200m", 80.0),
        ("central_sh1800", "Central SH1800", 310.0),
        ("bateria", "Bateria", 83.0),
        ("sirene", "Sirene", 2.0),
        ("concertina_10m", "Concertina 30cm (10m)", 90.0),
        ("concertina_linear_20m", "Concertina linear (20m)", 53.0),
        ("kit_isoladores", "Kit isoladores (100 un)", 19.9),
        ("cabo_alta_50m", "Cabo de alta isolação (50m)", 75.0),
        ("kit_placas", "Kit placas aviso", 19.0),
        ("kit_aterramento", "Kit aterramento", 165.0),

        # Mão de obra proporcional
        ("mao_cerca_base", "Mão de obra cerca (base)", 250.0),
        ("mao_cerca_m", "Mão de obra cerca (R$/m)", 18.0),
        ("mao_concertina_base", "Mão de obra concertina (base)", 150.0),
        ("mao_concertina_m", "Mão de obra concertina (R$/m)", 8.0),
        ("mao_linear_base", "Mão de obra linear (base)", 200.0),
        ("mao_linear_m", "Mão de obra linear (R$/m)", 10.0),
    ]

    for k, d, v in seeds:
        if not conn.execute("SELECT 1 FROM precos WHERE chave=?", (k,)).fetchone():
            set_preco(conn, k, d, v)


# =========================================================
# HELPERS
# =========================================================
def brl(v):
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def add_item(itens, subtotal, conn, chave, qtd, label=None):
    unit = get_preco(conn, chave)
    sub = unit * qtd
    itens.append((label or chave, qtd, unit, sub))
    return subtotal + sub


def ceil_div(a, b):
    return int((a + b - 1) // b)


def mao_por_m(conn, base_key, m_key, perimetro):
    base = get_preco(conn, base_key)
    por_m = get_preco(conn, m_key)
    return base, por_m, base + (perimetro * por_m)


# =========================================================
# PDF COMPLETO
# =========================================================
def gerar_pdf_completo(out, cliente, servico, resumo, itens, subtotal, desconto, total, pagamento):
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4

    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 120, width=80, height=80)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, h - 70, EMPRESA)
    c.setFont("Helvetica", 10)
    c.drawString(140, h - 90, f"WhatsApp: {WHATSAPP}")
    c.drawString(140, h - 105, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    y = h - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Orçamento")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 16
    c.drawString(40, y, f"Serviço: {servico}")

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "O que será entregue")
    y -= 16
    c.setFont("Helvetica", 10)
    for l in resumo.split("\n"):
        c.drawString(40, y, l)
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Descrição")
    c.drawString(300, y, "Qtd")
    c.drawString(360, y, "Unit")
    c.drawString(440, y, "Subtotal")
    y -= 8
    c.line(40, y, 550, y)
    y -= 14

    c.setFont("Helvetica", 9)
    for d, q, u, s in itens:
        c.drawString(40, y, d[:40])
        c.drawRightString(330, y, str(q))
        c.drawRightString(410, y, brl(u))
        c.drawRightString(550, y, brl(s))
        y -= 14

    y -= 10
    c.line(40, y, 550, y)
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(550, y, f"Subtotal: {brl(subtotal)}")
    y -= 14
    if desconto > 0:
        c.drawRightString(550, y, f"Desconto: - {brl(desconto)}")
        y -= 14
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"TOTAL: {brl(total)}")

    y -= 28
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 14
    c.drawString(40, y, f"Garantia: {GARANTIA_PADRAO} | Validade: {VALIDADE_PADRAO} dias")

    c.save()


# =========================================================
# PDF RESUMIDO (BONITO)
# =========================================================
def gerar_pdf_resumido(out, cliente, servico, texto, total, pagamento):
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4

    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 120, width=80, height=80)

    c.setFont("Helvetica-Bold", 18)
    c.drawString(140, h - 70, EMPRESA)
    c.setFont("Helvetica", 10)
    c.drawString(140, h - 90, f"WhatsApp: {WHATSAPP}")
    c.drawString(140, h - 105, f"Data: {datetime.now().strftime('%d/%m/%Y')}")

    y = h - 170
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Orçamento (Resumo)")
    y -= 24

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Cliente: {cliente}")
    y -= 16
    c.drawString(40, y, f"Serviço: {servico}")

    y -= 24
    c.setFont("Helvetica", 10)
    for l in texto.split("\n"):
        c.drawString(40, y, l)
        y -= 14

    y -= 30
    c.setFont("Helvetica-Bold", 28)
    c.drawString(40, y, brl(total))

    y -= 40
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Pagamento: {pagamento}")
    y -= 14
    c.drawString(40, y, f"Garantia: {GARANTIA_PADRAO} | Validade: {VALIDADE_PADRAO} dias")
    y -= 20
    c.drawString(40, y, f"Para confirmar, fale no WhatsApp: {WHATSAPP}")

    c.save()


# =========================================================
# APP
# =========================================================
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.title("🧾 Gerador de Orçamentos — RR Smart Soluções")

conn = db()
ensure_seed(conn)

menu = st.sidebar.radio("Menu", ["Gerar orçamento", "Editar preços"])

if menu == "Editar preços":
    st.subheader("Tabela de preços")
    rows = list_precos(conn)
    with st.form("precos"):
        for k, d, v in rows:
            new = st.number_input(d, value=float(v))
            set_preco(conn, k, d, new)
        st.form_submit_button("Salvar")

else:
    cliente = st.text_input("Cliente")
    servico = st.selectbox(
        "Serviço",
        [
            "Cerca elétrica (instalação)",
            "Cerca elétrica + concertina",
            "Concertina linear eletrificada",
        ],
    )

    perimetro = st.number_input("Perímetro (m)", value=36.0)
    desconto_tipo = st.selectbox("Desconto", ["Sem desconto", "%", "R$"])
    desconto_val = st.number_input("Valor do desconto", value=0.0)
    pagamento = st.text_input("Pagamento", "50% entrada e 50% após finalizar")

    tipo_pdf = st.radio("Tipo de PDF", ["Completo", "Resumido"])

    if st.button("Gerar PDF"):
        itens = []
        subtotal = 0.0

        if "Cerca elétrica" in servico:
            subtotal = add_item(itens, subtotal, conn, "central_sh1800", 1, "Central")
            base, m, mao = mao_por_m(conn, "mao_cerca_base", "mao_cerca_m", perimetro)
            subtotal += mao
            itens.append(("Mão de obra", perimetro, m, mao))
            texto = f"Instalação de cerca elétrica em {perimetro:.0f}m.\nSistema completo e funcional."

        elif "Concertina linear" in servico:
            subtotal = add_item(itens, subtotal, conn, "concertina_linear_20m", ceil_div(perimetro, 20), "Concertina")
            base, m, mao = mao_por_m(conn, "mao_linear_base", "mao_linear_m", perimetro)
            subtotal += mao
            itens.append(("Mão de obra", perimetro, m, mao))
            texto = f"Instalação de concertina linear eletrificada em {perimetro:.0f}m."

        desconto = 0.0
        if desconto_tipo == "%":
            desconto = subtotal * (desconto_val / 100)
        elif desconto_tipo == "R$":
            desconto = desconto_val

        total = max(0, subtotal - desconto)

        os.makedirs("output", exist_ok=True)
        nome = cliente.replace(" ", "_")
        out = f"output/orcamento_{nome}.pdf"

        if tipo_pdf == "Completo":
            gerar_pdf_completo(out, cliente, servico, texto, itens, subtotal, desconto, total, pagamento)
        else:
            gerar_pdf_resumido(out, cliente, servico, texto, total, pagamento)

        with open(out, "rb") as f:
            st.download_button("Baixar PDF", f, file_name=os.path.basename(out))
