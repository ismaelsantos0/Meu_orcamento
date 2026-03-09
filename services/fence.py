import math

def calcular_cerca_completa(metros: float, distancia_haste: float, tipo: str, tem_central: bool, materiais_db: dict):
    itens = []
    
    # Função auxiliar poderosa: Busca o Nome e o Preço pelo ID (slug) direto do Banco de Dados
    def adicionar_item_pelo_id(slug: str, quantidade: float):
        # Fallbacks de segurança caso alguém apague o item do banco por acidente
        fallbacks = {
            "haste_cerca": {"nome": "Haste de Cerca 1m", "preco": 19.00},
            "fio_aco": {"nome": "Fio de Aço (Rolo)", "preco": 80.00},
            "concertina_30cm": {"nome": "Rolo Concertina 30cm (10m)", "preco": 90.00},
            "concertina_linear": {"nome": "Rolo Concertina Linear (20m - 6 fios)", "preco": 53.00},
            "central_sh1800": {"nome": "Central SH1800", "preco": 310.00},
            "bateria": {"nome": "Bateria 7A", "preco": 83.00},
            "sirene": {"nome": "Sirene", "preco": 2.00},
            "kit_aterramento": {"nome": "Kit Aterramento", "preco": 45.00}
        }
        
        # Tenta pegar do banco, se não achar, usa o fallback de segurança
        item = materiais_db.get(slug, fallbacks.get(slug))
        if item:
            itens.append({
                "nome": item["nome"],            # O NOME vem do banco de dados!
                "quantidade": quantidade,
                "preco_unitario": item["preco"]  # O PREÇO vem do banco de dados!
            })

    # 1. Cálculo de Hastes
    qtd_hastes = math.ceil(metros / distancia_haste) + 1
    adicionar_item_pelo_id("haste_cerca", qtd_hastes)

    # 2. Lógica de Tipo com valores exatos
    # Convertendo para evitar falhas de digitação do Frontend
    tipo_seguro = str(tipo).strip().lower()

    if tipo_seguro == "simples":
        adicionar_item_pelo_id("fio_aco", 1)
        
    elif tipo_seguro == "concertina_linear":
        qtd_rolos = math.ceil((metros * 6) / 20)
        adicionar_item_pelo_id("concertina_linear", qtd_rolos)

    elif tipo_seguro == "com_concertina":
        qtd_rolos = math.ceil(metros / 10)
        adicionar_item_pelo_id("concertina_30cm", qtd_rolos)

    # 3. Kit Central e Periféricos
    is_central = str(tem_central).lower() == 'true'
    if is_central:
        adicionar_item_pelo_id("central_sh1800", 1)
        adicionar_item_pelo_id("bateria", 1)
        adicionar_item_pelo_id("sirene", 1)
        adicionar_item_pelo_id("kit_aterramento", 1)

    total_materiais = sum(i["quantidade"] * i["preco_unitario"] for i in itens)
    
    return {
        "itens": itens,
        "total_materiais": total_materiais
    }
