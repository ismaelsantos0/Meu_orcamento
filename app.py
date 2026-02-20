# app.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from core.materials import build_materials_list, materials_text_for_whatsapp
from core.db import get_conn  # Importação vitalícia para conectar ao PostgreSQL


# =========================
# Registry de serviços (plugins)
# =========================
import services.registry as registry


def load_plugins():
    """
    Suporta registry nos formatos:
    - get_plugins() -> dict | list
    - REGISTRY (dict)
    - PLUGINS (dict)
    - plugins (dict | list)
    """
    if hasattr(registry, "get_plugins") and callable(getattr(registry, "get_plugins")):
        plugins = registry.get_plugins()
    elif hasattr(registry, "REGISTRY"):
        plugins = registry.REGISTRY
    elif hasattr(registry, "PLUGINS"):
        plugins = registry.PLUGINS
    elif hasattr(registry, "plugins"):
        plugins = registry.plugins
    else:
        raise RuntimeError(
            "Não encontrei plugins no services/registry.py "
            "(esperado: get_plugins(), REGISTRY, PLUGINS ou plugins)"
        )

    if isinstance(plugins, dict):
        return list(plugins.values())

    return list(plugins)


# =========================
# PDF - Wrapper (ajuste 1x se necessário)
# =========================
def generate_pdf_bytes(quote: dict, *, logo_path: str | None = None) -> bytes:
    """
    Tenta gerar PDF usando core/pdf/pdf.py.
    """
    from core.pdf import pdf as pdfmod  # core/pdf/pdf.py

    # Nomes comuns de função
    for fn_name in ("render_quote_pdf", "render_pdf", "generate_pdf", "build_pdf", "make_pdf", "create_pdf"):
        fn = getattr(pdfmod, fn_name, None)
        if callable(fn):
            try:
                return fn(quote, logo_path=logo_path)  # type: ignore
            except TypeError:
                return fn(quote)  # type: ignore

    raise RuntimeError(
        "Não encontrei função de PDF em core/pdf/pdf.py. "
        "Abra esse arquivo e veja o nome da função que gera o PDF."
    )


# =========================
# Helpers
# =========================
def brl(v: float) -> str:
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="Gerador de Orçamentos", page_icon="🧾", layout="wide")

ASSETS_DIR = Path(__file__).parent / "assets"
DEFAULT_LOGO = ASSETS_DIR / "logo.png"

st.title("🧾 Gerador de Orçamentos")

# Sidebar: configurações
with st.sidebar:
    st.header("Configurações")
    usar_logo = st.checkbox("Usar logo no PDF", value=DEFAULT_LOGO.exists())
    logo_path = str(DEFAULT_LOGO) if usar_logo and DEFAULT_LOGO.exists() else None

    st.divider()
    st.subheader("Dados do cliente (opcional)")
    cliente_nome = st.text_input("Nome do cliente", value="")
    cliente_tel = st.text_input("Telefone/WhatsApp", value="")
    obs_geral = st.text_area("Observações gerais", value="", height=90)

# Carrega plugins
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

st.caption(f"Serviço selecionado: **{plugin.label}** •  ID: `{plugin.id}`")

# Campos do serviço
st.subheader("Dados do serviço")
inputs = plugin.render_fields()

colA, colB = st.columns([1, 2])
with colA:
    gerar = st.button("✅ Gerar orçamento", use_container_width=True)
with colB:
    st.info("Gere o orçamento → baixe o PDF → gere a lista de materiais para mandar na loja.")

if not gerar:
    st.stop()

# =========================
# Conexão DB
# =========================
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Falha ao conectar no banco de dados: {e}")
    st.stop()

# =========================
# Calcula orçamento
# =========================
try:
    quote = plugin.compute(conn, inputs)
except Exception as e:
    st.error(f"Erro ao calcular itens do orçamento. Verifique os preços no banco: {e}")
    st.stop()

# Injeta dados do cliente
quote["client_name"] = cliente_nome
quote["client_phone"] = cliente_tel
quote["notes"] = obs_geral

# =========================
# Itens
# =========================
st.subheader("Itens do orçamento")
items_df = pd.DataFrame(quote.get("items", []))
if not items_df.empty:
    st.dataframe(items_df, use_container_width=True)
else:
    st.warning("Nenhum item retornado pelo serviço.")

subtotal = float(quote.get("subtotal", 0.0))
st.markdown(f"### Total: **{brl(subtotal)}**")

# =========================
# PDF
# =========================
st.divider()
st.subheader("📄 PDF do orçamento")

# O botão do Streamlit para download não precisa do try/except no clique como um botão normal
try:
    pdf_bytes = generate_pdf_bytes(quote, logo_path=logo_path)
    filename = f"orcamento_{plugin.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    st.download_button(
        "⬇️ Baixar PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        use_container_width=True,
    )
except Exception as e:
    st.error(f"Erro ao gerar o arquivo PDF: {e}")

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

if not materials:
    st.warning("Não encontrei materiais para listar com as regras atuais.")
else:
    mats_df = pd.DataFrame(materials)
    st.dataframe(mats_df, use_container_width=True)

    text = materials_text_for_whatsapp(
        materials,
        header_lines=[
            f"Serviço: {quote.get('service_name', '')}",
            f"Cliente: {cliente_nome}" if cliente_nome else "Cliente: (não informado)",
            f"Data: {datetime.now().strftime('%d/%m/%Y')}",
        ],
    )

    st.text_area("Texto para enviar no WhatsApp (copiar/colar)", text, height=220)

    csv = mats_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV da lista de materiais",
        data=csv,
        file_name=f"lista_materiais_{plugin.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
