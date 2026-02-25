import streamlit as st
import pandas as pd
import time

# O Dicionário com os IDs exatos que os seus plugins usam (NÃO ALTERAR AS CHAVES)
CATALOGO_SISTEMA = {
    "haste_reta": ("Haste reta", "Cerca/Concertina"),
    "haste_canto": ("Haste de canto", "Cerca/Concertina"),
    "concertina_linear_20m": ("Concertina linear (20m)", "Cerca/Concertina"),
    "concertina_10m": ("Concertina 30cm (10m)", "Cerca/Concertina"),
    "fio_aco_200m": ("Fio de aço (200m)", "Cerca/Concertina"),
    "central_sh1800": ("Central SH1800", "Cerca/Concertina"),
    "bateria": ("Bateria 12V", "Cerca/Concertina"),
    "sirene": ("Sirene", "Cerca/Concertina"),
    "cabo_alta_50m": ("Cabo de alta isolação (50m)", "Cerca/Concertina"),
    "kit_aterramento": ("Kit Aterramento", "Cerca/Concertina"),
    "kit_placas": ("Kit Placas de Aviso", "Cerca/Concertina"),
    "kit_isoladores": ("Kit Isoladores (100un)", "Cerca/Concertina"),
    "mao_linear_base": ("Mão de obra: Concertina Linear (Base)", "Cerca/Concertina"),
    "mao_linear_por_m": ("Mão de obra: Concertina Linear (Metro)", "Cerca/Concertina"),
    "mao_cerca_base": ("Mão de obra: Cerca Elétrica (Base)", "Cerca/Concertina"),
    "mao_cerca_por_m": ("Mão de obra: Cerca Elétrica (Metro)", "Cerca/Concertina"),
    "mao_concertina_base": ("Mão de obra: Concertina em Cerca (Base)", "Cerca/Concertina"),
    "mao_concertina_por_m": ("Mão de obra: Concertina em Cerca (Metro)", "Cerca/Concertina"),
    "cftv_camera": ("Câmera CFTV", "CFTV"),
    "cftv_dvr": ("DVR", "CFTV"),
    "cftv_hd": ("HD para DVR", "CFTV"),
    "cftv_fonte_colmeia": ("Fonte Colmeia", "CFTV"),
    "cftv_cabo_cat5_m": ("Cabo Cat5e (Metro)", "CFTV"),
    "cftv_balun": ("Balun de Vídeo", "CFTV"),
    "cftv_conector_p4_macho": ("Conector P4 Macho", "CFTV"),
    "cftv_conector_p4_femea": ("Conector P4 Fêmea", "CFTV"),
    "cftv_suporte_camera": ("Suporte para Câmera", "CFTV"),
    "cftv_caixa_hermetica": ("Caixa Hermética", "CFTV"),
    "mao_cftv_dvr": ("Mão de obra: Instalação DVR", "CFTV"),
    "mao_cftv_por_camera_inst": ("Mão de obra: Instalar Câmera (un)", "CFTV"),
    "mao_cftv_por_camera_defeito": ("Mão de obra: Manutenção Câmera", "CFTV"),
    "mao_motor_inst": ("Mão de obra: Instalação Motor", "Motor de Portão"),
    "mao_motor_man": ("Mão de obra: Manutenção Motor", "Motor de Portão")
}

def restaurar_catalogo_base(conn, user_id):
    """Garante que todos os IDs exigidos pelos plugins existam no banco do usuário."""
    with conn.cursor() as cur:
        for chave, (nome, cat) in CATALOGO_SISTEMA.items():
            cur.execute("SELECT id FROM precos WHERE chave = %s AND usuario_id = %s", (chave, user_id))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO precos (chave, nome, valor, usuario_id, categoria) 
                    VALUES (%s, %s, 0.0, %s, %s)
                """, (chave, nome, user_id, cat))
    conn.commit()

def render_precos(conn, user_id):
    st.header("Gestão de Preços e Serviços")
    
    # Executa a garantia de que as chaves existem
    restaurar_catalogo_base(conn, user_id)
    
    if 'msg_sucesso' in st.session_state:
        st.success(st.session_state.msg_sucesso)
        del st.session_state.msg_sucesso 
    
    with st.container(border=True):
        st.write("Atualize os valores dos itens do sistema ou adicione itens extras.")
        
        with conn.cursor() as cur:
            cur.execute("SELECT chave, nome, valor, categoria FROM precos WHERE usuario_id = %s ORDER BY nome ASC", (user_id,))
            todos_itens = cur.fetchall()
            
        opcoes_itens = {"[CRIAR NOVO ITEM EXTRA]": ""}
        for item in todos_itens:
            opcoes_itens[f"{item[1]} (Atual: R$ {float(item[2]):.2f})"] = item[0]

        sel_item = st.selectbox("Selecione o item para precificar:", list(opcoes_itens.keys()))
        chave_selecionada = opcoes_itens[sel_item]
        
        item_atual = next((i for i in todos_itens if i[0] == chave_selecionada), None)
        nome_default = item_atual[1] if item_atual else ""
        valor_default = float(item_atual[2]) if item_atual else 0.0
        cat_default = item_atual[3] if item_atual else "Geral"
        
        c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
        
        # Bloqueia a edição do nome se for um ID nativo do sistema para não quebrar a organização
        bloquear_nome = chave_selecionada in CATALOGO_SISTEMA

        p_nm = c_p1.text_input("Nome do Produto", value=nome_default, disabled=bloquear_nome)
        p_vl = c_p2.number_input("Preço R$", min_value=0.0, value=valor_default)
        p_ct = c_p3.selectbox("Categoria", ["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"], index=["CFTV", "Cerca/Concertina", "Motor de Portão", "Geral"].index(cat_default), disabled=bloquear_nome)
        
        if st.button("SALVAR PREÇO", use_container_width=True):
            if p_nm:
                with conn.cursor() as cur:
                    if chave_selecionada:
                        # Se for item do sistema, atualiza só o preço
                        if bloquear_nome:
                            cur.execute("UPDATE precos SET valor = %s WHERE chave = %s AND usuario_id = %s", (p_vl, chave_selecionada, user_id))
                        else:
                            cur.execute("UPDATE precos SET nome = %s, valor = %s, categoria = %s WHERE chave = %s AND usuario_id = %s", (p_nm, p_vl, p_ct, chave_selecionada, user_id))
                        msg = f"✅ Preço atualizado para R$ {p_vl:.2f}!"
                    else:
                        chave_automatica = f"EXTRA_{int(time.time())}"
                        cur.execute("INSERT INTO precos (chave, nome, valor, usuario_id, categoria) VALUES (%s, %s, %s, %s, %s)", (chave_automatica, p_nm, p_vl, user_id, p_ct))
                        msg = f"✅ Novo extra '{p_nm}' adicionado!"
                conn.commit()
                st.session_state.msg_sucesso = msg
                st.rerun()
            else:
                st.warning("Preencha o nome.")

    st.markdown("---")
    st.markdown("### Tabela de Custos")
    df_lista = pd.read_sql("SELECT chave as \"ID do Sistema\", nome as \"Produto\", valor as \"Preço (R$)\", categoria as \"Categoria\" FROM precos WHERE usuario_id = %s ORDER BY categoria, nome", conn, params=(user_id,))
    st.dataframe(df_lista, use_container_width=True, hide_index=True)
