import os
import sqlite3
from datetime import datetime
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

APP_TITLE = "RR Smart Soluções — Gerador de Orçamentos"
DB_PATH = "data/db.sqlite"
LOGO_PATH = "assets/logo.png"
EMPRESA = "RR Smart Soluções"
GARANTIA_PADRAO = "6 meses"
WHATSAPP = "(95) 98418-7832"  # troque

# --------------------
# DB
# --------------------
def db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            chave TEXT PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL
        )
    """)
    return conn

def get_preco(conn, chave, default=0.0):
    cur = conn.execute("SELECT valor FROM precos WHERE chave=?", (chave,))
    row = cur.fetchone()
    return float(row[0]) if row else float(default)

def set_preco(conn, chave, descricao, valor):
    conn.execute("""
        INSERT INTO precos (chave, descricao, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE SET descricao=excluded.descricao, valor=excluded.valor
    """, (chave, descricao, float(valor)))
    conn.commit()

def list_precos(conn):
    cur = conn.execute("SELECT chave, descricao, valor FROM precos ORDER BY chave")
    return cur.fetchall()

# --------------------
# PDF
# --------------------
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
    validade_dias: int = 7
):
    c = canvas.Canvas(out_path, pagesize=A4)
    w, h = A4

    # Header
    y = h - 60
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, 40, h - 120, width=80, height=80, mask='auto')
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
        c.drawString(40, y, line.strip())
        y -= 14

    # Itens
    y -= 10
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
            y = h - 60
            c.setFont("Helvetica", 9)
        c.drawString(40, y, str(desc)[:45])
        c.drawRightString(330, y, f"{qtd}")
        c.drawRightString(410, y, f"R$ {unit:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        c.drawRightString(550, y, f"R$ {sub:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        y -= 14

    # Totais
    y -= 10
    c.line(40, y, 550, y)
    y -= 18
    c.setFont("Helvetica-Bold", 10)
    fmt = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c.drawRightString(550, y, f"Subtotal: {fmt(subtotal)}")
    y -= 14
    if desconto_valor > 0:
        c.drawRightString(550, y, f"Desconto ({desconto_label}): - {fmt(desconto_valor)}")
        y -= 14
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(550, y, f"TOTAL: {fmt(total)}")

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

# --------------------
# App
# --------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.title("🧾 Gerador de Orçamentos — RR Smart Soluções")

conn = db()

menu = st.sidebar.radio("Menu", ["Gerar orçamento", "Editar preços"])

# Seed básico (você troca depois)
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
    ]
    for k, d, v in seeds:
        set_preco(conn, k, d, v)

if menu == "Editar preços":
    st.subheader("💲 Tabela de preços (editável)")
    rows = list_precos(conn)

    with st.form("form_precos"):
        cols = st.columns([2, 5, 2])
        st.caption("Dica: altere os valores aqui e o gerador usa automaticamente.")
        updated = []
        for chave, desc, val in rows:
            c1, c2, c3 = st.columns([2, 6, 2])
            with c1:
                st.text_input("Chave", value=chave, key=f"k_{chave}", disabled=True)
            with c2:
                new_desc = st.text_input("Descrição", value=desc, key=f"d_{chave}")
            with c3:
                new_val = st.number_input("Valor (R$)", value=float(val), min_value=0.0, step=1.0, key=f"v_{chave}")
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
        telefone = st.text_input("Telefone / WhatsApp (opcional)", placeholder="Ex.: (95) 9xxxx-xxxx")
    with colB:
        tipo = st.selectbox("Tipo de serviço", [
            "Cerca elétrica (instalação)",
            "Cerca elétrica + concertina (instalação)",
            "Concertina linear eletrificada (instalação)",
            "Cerca elétrica (manutenção)",
            "Câmeras (instalação)",
            "Câmeras (manutenção)",
            "Motor de portão (instalação)",
            "Motor de portão (manutenção)",
        ])
        garantia = st.text_input("Garantia", value=GARANTIA_PADRAO)

    st.divider()

    # Campos específicos para cerca
    perimetro = 36.0
    fios = 6
    espacamento = 2.5

    if "Cerca" in tipo or "Concertina" in tipo:
        c1, c2, c3 = st.columns(3)
        with c1:
            perimetro = st.number_input("Perímetro (m)", value=36.0, min_value=1.0, step=1.0)
        with c2:
            fios = st.number_input("Qtd. fios", value=6, min_value=1, step=1)
        with c3:
            espacamento = st.number_input("Espaçamento entre hastes (m)", value=2.5, min_value=0.5, step=0.1)

    desconto_tipo = st.selectbox("Desconto", ["Sem desconto", "%", "R$"])
    desconto_val = 0.0
    if desconto_tipo != "Sem desconto":
        desconto_val = st.number_input("Valor do desconto", value=0.0, min_value=0.0, step=10.0)

    pagamento = st.text_input("Condição de pagamento", value="50% de entrada e 50% após finalizar o serviço")

    if st.button("Gerar PDF"):
        if not cliente.strip():
            st.error("Informe o nome do cliente.")
            st.stop()

        itens = []
        subtotal = 0.0

        # Lógica simplificada para CERCA/CONCERTINA (você pode expandir depois)
        if tipo.startswith("Cerca elétrica"):
            # Quantidades
            hastes_total = int((perimetro / espacamento) + 0.999) + 1  # aproxima e fecha
            hastes_canto = 4
            hastes_retas = max(0, hastes_total - hastes_canto)

            arame_m = perimetro * fios
            rolos_fio = 2 if arame_m > 200 else 1  # simples pro MVP

            # Itens materiais
            def add(chave, qtd, label=None):
                nonlocal subtotal
                unit = get_preco(conn, chave)
                desc = label or chave
                sub = unit * qtd
                itens.append((desc, qtd, unit, sub))
                subtotal += sub

            add("haste_reta", hastes_retas, "Haste reta")
            add("haste_canto", hastes_canto, "Haste de canto")
            add("fio_aco_200m", rolos_fio, "Fio de aço (rolo 200m)")
            add("central_sh1800", 1, "Central SH1800")
            add("bateria", 1, "Bateria")
            add("sirene", 1, "Sirene")

            # Complementos
            add("kit_isoladores", 1, "Kit isoladores (100 un)")
            add("cabo_alta_50m", 1, "Cabo alta isolação (50m)")
            add("kit_placas", 1, "Kit placas aviso")
            add("kit_aterramento", 1, "Kit aterramento")

            # Mão de obra
            mao = get_preco(conn, "mao_obra_cerca")
            itens.append(("Mão de obra (instalação)", 1, mao, mao))
            subtotal += mao

            # Concertina extra
            if "+ concertina" in tipo:
                rolos = int((perimetro / 10) + 0.999)
                unit = get_preco(conn, "concertina_10m")
                sub = unit * rolos
                itens.append(("Concertina 30cm (rolo 10m)", rolos, unit, sub))
                subtotal += sub

                mao2 = get_preco(conn, "mao_obra_concertina")
                itens.append(("Mão de obra (instalação concertina)", 1, mao2, mao2))
                subtotal += mao2

        elif tipo.startswith("Concertina linear"):
            # Concertina linear substitui fios, mas mantém central/sirene/bateria/aterramento/placas
            rolos = int((perimetro / 20) + 0.999)
            unit = get_preco(conn, "concertina_linear_20m")
            sub = unit * rolos
            itens.append(("Concertina linear (rolo 20m)", rolos, unit, sub))
            subtotal += sub

            # Sistema
            for k, d in [
                ("central_sh1800", "Central SH1800"),
                ("bateria", "Bateria"),
                ("sirene", "Sirene"),
                ("cabo_alta_50m", "Cabo alta isolação (50m)"),
                ("kit_aterramento", "Kit aterramento"),
                ("kit_placas", "Kit placas aviso"),
            ]:
                unit = get_preco(conn, k)
                itens.append((d, 1, unit, unit))
                subtotal += unit

            mao = get_preco(conn, "mao_obra_concertina_linear")
            itens.append(("Mão de obra (instalação)", 1, mao, mao))
            subtotal += mao

        else:
            # Outros serviços: por enquanto só mão de obra (você depois cria kits)
            # Crie chaves específicas no menu "Editar preços" e puxe aqui.
            itens.append((f"Serviço: {tipo}", 1, 0.0, 0.0))

        # Desconto
        desconto_valor = 0.0
        desconto_label = "—"
        if desconto_tipo == "%":
            desconto_label = f"{desconto_val:.2f}%"
            desconto_valor = subtotal * (desconto_val / 100.0)
        elif desconto_tipo == "R$":
            desconto_label = "R$"
            desconto_valor = min(desconto_val, subtotal)

        total = max(0.0, subtotal - desconto_valor)

        resumo = ""
        if "Cerca elétrica (instalação)" in tipo:
            resumo = (
                "Instalação completa de cerca elétrica em todo o perímetro,\n"
                f"com {fios} fios, hastes espaçadas em {espacamento}m, sistema entregue\n"
                "funcionando, com aterramento, placas de aviso, testes e regulagem."
            )
        elif "cerca elétrica + concertina" in tipo.lower():
            resumo = (
                "Instalação completa de cerca elétrica + concertina em todo o perímetro,\n"
                "com sistema entregue funcionando, aterramento, placas de aviso e testes finais."
            )
        elif "Concertina linear eletrificada" in tipo:
            resumo = (
                "Instalação de concertina linear eletrificada em todo o perímetro,\n"
                "mantendo central, bateria, sirene e sistema de alarme, com aterramento\n"
                "e testes finais de funcionamento."
            )
        else:
            resumo = "Serviço conforme combinado, com entrega testada e orientações ao cliente."

        os.makedirs("output", exist_ok=True)
        out = f"output/orcamento_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        gerar_pdf_orcamento(
            out_path=out,
            cliente=f"{cliente}  ({telefone})" if telefone.strip() else cliente,
            servico=tipo,
            resumo_entrega=resumo,
            itens=itens,
            subtotal=subtotal,
            desconto_label=desconto_label,
            desconto_valor=desconto_valor,
            total=total,
            pagamento=pagamento,
            garantia=garantia,
        )

        st.success("PDF gerado!")
        with open(out, "rb") as f:
            st.download_button("Baixar orçamento (PDF)", f, file_name=os.path.basename(out), mime="application/pdf")
