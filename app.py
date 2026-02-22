# app.py
from __future__ import annotations

import io
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from core.materials import build_materials_list, materials_text_for_whatsapp
from core.db import get_conn


# =========================
# Registry de serviços (plugins)
# =========================
import services.registry as registry

def load_plugins():
    if hasattr(registry, "get_plugins") and callable(getattr(registry, "get_plugins")):
        plugins = registry.get_plugins()
    elif hasattr(registry, "REGISTRY"):
        plugins = registry.REGISTRY
    elif hasattr(registry, "PLUGINS"):
        plugins = registry.PLUGINS
    elif hasattr(registry, "plugins"):
        plugins = registry.plugins
    else:
        raise RuntimeError("Não encontrei plugins no services/registry.py")

    if isinstance(plugins, dict):
        return list(plugins.values())
    return list(plugins)


# =========================
# PDF - Wrapper Atualizado
# =========================
def generate_pdf_bytes(single_quote: dict, tipo: str = "summary", logo_path: str | None = None) -> bytes:
    """
    Gera o PDF. Focado agora na proposta comercial e recuperando textos ricos.
    """
    # Resgata a descrição rica, itens inclusos e vantagens!
    if "summary_full" not in single_quote:
        desc = single_quote.get("service_description", {})
        if isinstance(desc, dict):
            texto_base = desc.get("description", "Serviço de instalação.")
            inclusos = desc.get("includes", [])
            vantagens = desc.get("advantages", [])
            
            texto_formatado = texto_base
            if inclusos:
                texto_formatado += "\n\nO que está incluso:\n• " + "\n• ".join(inclusos)
            if vantagens:
                texto_formatado += "\n\nPrincipais Vantagens:\n• " + "\n• ".join(vantagens)
                
            single_quote["summary_full"] = texto_formatado
            single_quote["summary_client"] = texto_formatado
        else:
            single_quote["summary_full"] = str(desc) if desc else "Serviço de instalação."
            single_quote["summary_client"] = str(desc) if desc else "Serviço de instalação."

    quote_for_pdf = {
        "logo_path": logo_path,
        "empresa": "RR Smart Soluções", 
        "whatsapp": single_quote.get("client_phone") or "(95) 98418-7832", 
        "data_str": datetime.now().strftime("%d/%m/%Y"),
        "cliente": single_quote.get("client_name") or "Cliente não informado",
        "servicos": [single_quote], 
        "subtotal": single_quote.get("subtotal", 0.0),
        "desconto_valor": 0.0,
        "desconto_label": "",
        "total": single_quote.get("subtotal", 0.0),
        "pagamento": "À vista ou 50% entrada / 50% na entrega", 
        "garantia": "Garantia de 90 dias",
        "validade_dias": 7
    }

    buffer = io.BytesIO()
    
    from core.pdf.summary import render_summary_pdf
    render_summary_pdf(buffer, quote_for_pdf)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# =========================
# Helpers
# =========================
def brl(v: float) -> str:
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# =========================
# Streamlit App Principal
# =========================
st.set_page_config(page_title="Gerador de Orçamentos", page_icon="🧾", layout="wide")

ASSETS_DIR = Path(__file__).parent / "assets"
DEFAULT_LOGO = ASSETS_DIR / "logo.png"

st.title("🧾 Gerador de Orçamentos")

with st.sidebar:
    st.header("Configurações")
    usar_logo = st.checkbox("Usar logo no PDF", value=DEFAULT_LOGO.exists())
    logo_path = str(DEFAULT_LOGO) if usar_logo and DEFAULT_LOGO.exists() else None

    st.divider()
    st.subheader("Dados do cliente (opcional)")
    cliente_nome = st.text_input("Nome do cliente", value="")
    cliente_tel = st.text_input("Telefone/WhatsApp do cliente", value="")
    obs_geral = st.text_area("Observações gerais", value="", height=90)

try:
    plugins = load_plugins()
except Exception as e:
    st.error(f"Erro carregando plugins: {e}")
    st.stop()

if not plugins:
    st.error("Nenhum serviço (plugin) encontrado em services/registry.py")
    st.stop()

plugin_by_label = {p.label: p for p in plugins}
service_label = st.selectbox("Selecione o serviço", options=list(plugin_by_label.keys()))
plugin = plugin_by_label[service_label]

st.caption(f"Serviço selecionado: **{plugin.label}** • ID: `{plugin.id}`")

try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()

st.subheader("Dados do serviço")
inputs = plugin.render_fields()

st.divider()
st.subheader("➕ Itens e Serviços Adicionais (Opcional)")
st.write("Selecione sensores, cabos extras, ou qualquer outro item avulso para somar neste orçamento.")

extras_to_add = []
try:
    with conn.cursor() as cur:
        cur.execute("SELECT chave, nome, valor FROM precos ORDER BY nome")
        db_items = cur.fetchall()
        
    items_dict = {}
    for row in db_items:
        chave = row[0]
        nome = row[1] if row[1] else chave.replace("_", " ").title()
        valor = float(row[2])
        label = f"{nome} (R$ {valor:.2f})"
        items_dict[label] = {"chave": chave, "nome": nome, "valor": valor}
        
    selected_extra_labels = st.multiselect("Selecione os itens extras", options=list(items_dict.keys()), placeholder="Buscar...")
    
    if selected_extra_labels:
        cols = st.columns(min(len(selected_extra_labels), 4))
        for i, label in enumerate(selected_extra_labels):
            with cols[i % 4]:
                qty = st.number_input(f"Qtd: {items_dict[label]['nome']}", min_value=1, value=1, step=1, key=f"extra_qty_{items_dict[label]['chave']}")
                extras_to_add.append({"item": items_dict[label], "qty": qty})

except Exception as e:
    st.error(f"Erro ao carregar itens extras: {e}")

st.divider()

colA, colB = st.columns([1, 2])
with colA:
    gerar = st.button("✅ Gerar orçamento", use_container_width=True, type="primary")
with colB:
    st.info("Preencha os dados acima e clique em Gerar orçamento.")

if not gerar:
    st.stop()

try:
    quote = plugin.compute(conn, inputs)
except Exception as e:
    st.error(f"Erro ao calcular itens do orçamento. Verifique os preços no banco: {e}")
    st.stop()

if extras_to_add:
    for extra in extras_to_add:
        item_data = extra["item"]
        qty = extra["qty"]
        sub = qty * item_data["valor"]
        
        quote["items"].append({"desc": f"[EXTRA] {item_data['nome']}", "qty": qty, "unit": item_data["valor"], "sub": sub})
        quote["subtotal"] += sub
        
    qtd_extras = len(extras_to_add)
    # Atualiza o summary_client com os itens adicionais antes de gerar o texto do WhatsApp
    if "summary_client" in quote:
        quote["summary_client"] += f"\n\nItens Adicionais Selecionados:\n• {qtd_extras} tipo(s) de item(ns) extra(s) incluso(s)."

quote["client_name"] = cliente_nome
quote["client_phone"] = cliente_tel
quote["notes"] = obs_geral

# =========================
# CONTROLE INTERNO (TELA)
# =========================
st.subheader("Seu Controle Interno (Custos e Quantidades)")
st.write("Estes dados são apenas para você conferir a matemática do serviço. Eles não aparecem no PDF.")
items_df = pd.DataFrame(quote.get("items", []))
if not items_df.empty:
    st.dataframe(items_df, use_container_width=True)
else:
    st.warning("Nenhum item retornado pelo serviço.")

subtotal = float(quote.get("subtotal", 0.0))
st.markdown(f"### Total Calculado: **{brl(subtotal)}**")

# =========================
# PDF E TEXTO WPP - MODO CLIENTE
# =========================
st.divider()
st.subheader("📄 Proposta Comercial (Para o Cliente)")
st.write("Use o botão abaixo para baixar o PDF ou copie o texto para enviar no WhatsApp.")

col_pdf, col_wpp = st.columns([1, 2])

with col_pdf:
    try:
        pdf_cliente = generate_pdf_bytes(quote, tipo="summary", logo_path=logo_path)
        st.download_button(
            label="🧑‍💼 Baixar Proposta em PDF",
            help="Gera o PDF com serviços, vantagens e valor total.",
            data=pdf_cliente,
            file_name=f"Proposta_{plugin.id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary" 
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF do Cliente: {e}")

with col_wpp:
    # Formata o texto para o WhatsApp usando * para negrito
    wpp_texto = f"🛡️ *RR Smart Soluções*\n\n"
    if cliente_nome:
        wpp_texto += f"Olá, *{cliente_nome}*! Segue a nossa proposta comercial:\n\n"
    else:
        wpp_texto += "Olá! Segue a nossa proposta comercial:\n\n"

    wpp_texto += f"🛠️ *Serviço:* {quote.get('service_name', '')}\n"
    
    # Pega o texto gerado (que já contém inclusos e vantagens, se existirem)
    desc_wpp = quote.get("summary_client", quote.get("summary_full", ""))
    if desc_wpp:
        wpp_texto += f"{desc_wpp}\n\n"

    wpp_texto += f"💰 *Investimento Total: {brl(subtotal)}*\n\n"
    wpp_texto += f"💳 *Condições de Pagamento:*\nÀ vista ou 50% entrada / 50% na entrega\n\n"
    wpp_texto += f"⚙️ *Garantia:* 90 dias\n"
    wpp_texto += f"⏳ *Validade do Orçamento:* 7 dias\n\n"
    wpp_texto += "Qualquer dúvida, estou à disposição para fecharmos o serviço! 🤝"
    
    st.text_area("💬 Copiar para WhatsApp", wpp_texto, height=250)


# =========================
# Lista de Materiais
# =========================
st.divider()
st.subheader("🧾 Lista de Materiais (para compra)")

only_materials = st.checkbox("Gerar somente materiais (sem mão de obra)", value=True)

materials = build_materials_list(
    quote,
    exclude_keywords=None if only_materials else [],
    group_same_desc=True,
)

if materials:
    mats_df = pd.DataFrame(materials)
    st.dataframe(mats_df, use_container_width=True)

    text_materiais = materials_text_for_whatsapp(
        materials,
        header_lines=[
            f"Serviço: {quote.get('service_name', '')}",
            f"Cliente: {cliente_nome}" if cliente_nome else "Cliente: (não informado)",
            f"Data: {datetime.now().strftime('%d/%m/%Y')}",
        ],
    )

    st.text_area("Lista de Peças (copiar/colar)", text_materiais, height=220)

    csv = mats_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV da lista de materiais",
        data=csv,
        file_name=f"lista_materiais_{plugin.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
