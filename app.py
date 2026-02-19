from core.materials import build_materials_list, materials_text_for_whatsapp
import pandas as pd

st.divider()
st.subheader("🧾 Lista de Materiais (para compra)")

if st.button("Gerar lista de materiais"):
    materials = build_materials_list(quote)

    if not materials:
        st.warning("Nenhum material encontrado.")
    else:
        df = pd.DataFrame(materials)
        st.dataframe(df, use_container_width=True)

        text = materials_text_for_whatsapp(
            materials,
            header_lines=[
                f"Serviço: {quote['service_name']}",
                f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}",
            ],
        )

        st.text_area("Texto para WhatsApp", text, height=220)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar CSV",
            data=csv,
            file_name="lista_materiais.csv",
            mime="text/csv",
        )
