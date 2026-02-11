import os
from datetime import datetime

import streamlit as st

from core.db import get_conn, ensure_seed, list_prices, save_prices_bulk
from core.pricing import apply_discount
from core.utils import make_pdf_name_multi
from core.pdf.complete import render_complete_pdf
from core.pdf.summary import render_summary_pdf

from services.registry import SERVICE_REGISTRY


APP_TITLE = "RR Smart Soluções — Gerador de Orçamentos"
EMPRESA = "RR Smart Soluções"
WHATSAPP = "97991728899"
LOGO_PATH = "assets/logo.png"
VALIDADE_PADRAO = 7
GARANTIA_PADRAO = "6 meses"


def _init_state():
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "quote_meta" not in st.session_state:
        st.session_state.quote_meta = {
            "cliente": "",
            "telefone": "",
            "garantia": GARANTIA_PADRAO,
            "pagamento": "50% de entrada e 50% após finalizar o serviço",
        }


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
    st.title("🧾 Gerador de Orçamentos — RR Smart Soluções")

    _init_state()

    conn = get_conn()
    ensure_seed(conn)

    menu = st.sidebar.radio("Menu", ["Gerar orçamento", "Editar preços"])

    if menu == "Editar preços":
        st.subheader("💲 Tabela de preços (editável)")
        rows = list_prices(conn)

        with st.form("form_prices"):
            st.caption("Altere valores e descrições. O gerador usa automaticamente.")
            edited = []
            for key, desc, val in rows:
                c1, c2, c3 = st.columns([2, 6, 2])
                with c1:
                    st.text_input("Chave", value=key, key=f"pk_{key}", disabled=True)
                with c2:
                    new_desc = st.text_input("Descrição", value=desc, key=f"pd_{key}")
                with c3:
                    new_val = st.number_input("Valor (R$)", value=float(val), min_value=0.0, step=1.0, key=f"pv_{key}")
                edited.append((key, new_desc, float(new_val)))

            if st.form_submit_button("Salvar alterações"):
                save_prices_bulk(conn, edited)
                st.success("Preços atualizados!")

        return

    # -------------------------
    # GERAR ORÇAMENTO (plugins + carrinho)
    # -------------------------
    st.subheader("🧾 Gerar orçamento (múltiplos serviços)")

    colA, colB = st.columns(2)
    with colA:
        st.session_state.quote_meta["cliente"] = st.text_input("Nome do cliente", value=st.session_state.quote_meta["cliente"])
        st.session_state.quote_meta["telefone"] = st.text_input("Telefone / WhatsApp (opcional)", value=st.session_state.quote_meta["telefone"])
    with colB:
        st.session_state.quote_meta["garantia"] = st.text_input("Garantia", value=st.session_state.quote_meta["garantia"])
        st.caption("Dica: você pode adicionar mais de um serviço antes de gerar o PDF.")

    st.divider()

    st.markdown("### ➕ Adicionar serviço ao orçamento")

    service_labels = [SERVICE_REGISTRY[k].label for k in SERVICE_REGISTRY]
    service_ids = list(SERVICE_REGISTRY.keys())

    selected_label = st.selectbox("Tipo de serviço", service_labels)
    selected_id = service_ids[service_labels.index(selected_label)]
    plugin = SERVICE_REGISTRY[selected_id]

    # Renderiza campos do plugin
    st.markdown(f"**Configurações do serviço:** {plugin.label}")
    inputs = plugin.render_fields()

    col_add, col_clear = st.columns([1, 1])
    with col_add:
        if st.button("Adicionar serviço"):
            price_map = conn  # o plugin vai ler via core.db.get_price(conn, key)
            svc = plugin.compute(conn, inputs)
            st.session_state.cart.append(svc)
            st.success(f"Serviço adicionado: {plugin.label}")

    with col_clear:
        if st.button("Limpar serviços"):
            st.session_state.cart = []
            st.info("Lista de serviços limpa.")

    st.divider()

    st.markdown("### 🧩 Serviços no orçamento")
    if not st.session_state.cart:
        st.caption("Nenhum serviço adicionado ainda.")
    else:
        subtotal_services = 0.0
        for i, s in enumerate(st.session_state.cart):
            c1, c2, c3 = st.columns([6, 2, 2])
            with c1:
                st.write(f"**{i+1}. {s['service_name']}**")
                if s.get("service_hint"):
                    st.caption(s["service_hint"])
            with c2:
                st.write(f"{s['subtotal_brl']}")
            with c3:
                if st.button("Remover", key=f"rm_{s['id']}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            subtotal_services += float(s["subtotal"])

        st.markdown(f"**Subtotal dos serviços:** {s['subtotal_brl'] if st.session_state.cart else 'R$ 0,00'}")
        st.write(f"Subtotal (numérico): R$ {subtotal_services:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.divider()

    st.markdown("### ✅ Finalizar orçamento")
    desconto_tipo = st.selectbox("Desconto", ["Sem desconto", "%", "R$"])
    desconto_val = 0.0
    if desconto_tipo != "Sem desconto":
        desconto_val = st.number_input("Valor do desconto", value=0.0, min_value=0.0, step=10.0)

    st.session_state.quote_meta["pagamento"] = st.text_input(
        "Condição de pagamento",
        value=st.session_state.quote_meta["pagamento"],
    )

    col_pdf1, col_pdf2 = st.columns(2)

    def _build_quote():
        cliente = st.session_state.quote_meta["cliente"].strip()
        telefone = st.session_state.quote_meta["telefone"].strip()
        garantia = st.session_state.quote_meta["garantia"].strip() or GARANTIA_PADRAO
        pagamento = st.session_state.quote_meta["pagamento"].strip()

        cliente_fmt = cliente
        if telefone:
            cliente_fmt = f"{cliente}  ({telefone})"

        subtotal = sum(float(s["subtotal"]) for s in st.session_state.cart)
        desconto_label, desconto_valor, total = apply_discount(subtotal, desconto_tipo, float(desconto_val))

        return {
            "empresa": EMPRESA,
            "whatsapp": WHATSAPP,
            "logo_path": LOGO_PATH,
            "cliente": cliente_fmt,
            "cliente_raw": cliente,
            "data_str": datetime.now().strftime("%d/%m/%Y"),
            "validade_dias": VALIDADE_PADRAO,
            "garantia": garantia,
            "pagamento": pagamento,
            "servicos": st.session_state.cart,
            "subtotal": subtotal,
            "desconto_label": desconto_label,
            "desconto_valor": desconto_valor,
            "total": total,
        }

    with col_pdf1:
        if st.button("Gerar PDF (Completo)"):
            if not st.session_state.quote_meta["cliente"].strip():
                st.error("Informe o nome do cliente.")
            elif not st.session_state.cart:
                st.error("Adicione pelo menos 1 serviço.")
            else:
                quote = _build_quote()
                os.makedirs("output", exist_ok=True)
                filename = make_pdf_name_multi(quote["cliente_raw"])
                out_path = os.path.join("output", filename)

                render_complete_pdf(out_path, quote)
                st.success("PDF completo gerado!")
                with open(out_path, "rb") as f:
                    st.download_button("Baixar PDF completo", f, file_name=filename, mime="application/pdf")

    with col_pdf2:
        if st.button("Gerar PDF (Resumido)"):
            if not st.session_state.quote_meta["cliente"].strip():
                st.error("Informe o nome do cliente.")
            elif not st.session_state.cart:
                st.error("Adicione pelo menos 1 serviço.")
            else:
                quote = _build_quote()
                os.makedirs("output", exist_ok=True)
                filename = make_pdf_name_multi(quote["cliente_raw"])
                out_path = os.path.join("output", filename)

                render_summary_pdf(out_path, quote)
                st.success("PDF resumido gerado!")
                with open(out_path, "rb") as f:
                    st.download_button("Baixar PDF resumido", f, file_name=filename, mime="application/pdf")


if __name__ == "__main__":
    main()
