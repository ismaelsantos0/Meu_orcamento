import math

def calcular_cerca_completa(metros: float, distancia_haste: float, tipo: str, tem_central: bool, materiais_db: dict):
    itens = []
    
    def adicionar_item_pelo_id(slug: str, quantidade: float):
        fallbacks = {
            "haste_cerca": {"nome": "Haste de Cerca 1m", "preco": 19.00},
            "haste_canto": {"nome": "Haste de Canto", "preco": 50.00},
            "fio_aco": {"nome": "Fio de Aço (Rolo 200m)", "preco": 80.00},
            "concertina_30cm": {"nome": "Rolo Concertina 30cm (10m)", "preco": 90.00},
            "concertina_linear": {"nome": "Rolo Concertina Linear (20m - 6 fios)", "preco": 53.00},
            "central_sh1800": {"nome": "Central SH1800", "preco": 310.00},
            "bateria": {"nome": "Bateria 7A", "preco": 83.00},
            "sirene": {"nome": "Sirene", "preco": 2.00},
            "kit_aterramento": {"nome": "Kit Aterramento", "preco": 45.00},
            "arame_galvanizado": {"nome": "Rolo Arame Galvanizado", "preco": 80.00},
            "fio_alta_tensao": {"nome": "Rolo Fio de Alta Tensão (50m)", "preco": 90.00},
            "fio_paralelo": {"nome": "Fio Paralelo (Metro)", "preco": 2.50},
            "fio_sirene": {"nome": "Fio para Sirene (Metro)", "preco": 4.00},
            "fio_aterramento": {"nome": "Fio para Aterramento (Metro)", "preco": 3.00}
        }
        
        item = materiais_db.get(slug, fallbacks.get(slug))
        if item and quantidade > 0:
            itens.append({
                "nome": item["nome"],
                "quantidade": quantidade,
                "preco_unitario": item["preco"]
            })

    # 1. Cálculo de Hastes Comuns
    qtd_hastes = math.ceil(metros / distancia_haste) + 1
    adicionar_item_pelo_id("haste_cerca", qtd_hastes)

    # 2. Lógica de Tipo (6 Fios e Regras Exatas)
    tipo_seguro = str(tipo).strip().lower()

    if tipo_seguro == "simples":
        # 6 fios no muro. Rolo rende 200m.
        qtd_rolos_fio = math.ceil((metros * 6) / 200)
        adicionar_item_pelo_id("fio_aco", qtd_rolos_fio)
        
    elif tipo_seguro == "concertina_linear":
        # Substitui o fio. 6 fios no muro. Rolo rende 20m.
        qtd_rolos_linear = math.ceil((metros * 6) / 20)
        adicionar_item_pelo_id("concertina_linear", qtd_rolos_linear)

    elif tipo_seguro == "com_concertina":
        # Combo: Fio (6 pernas) + Concertina (rolo 10m) + Arame de sustentação (rolo 50m)
        qtd_rolos_fio = math.ceil((metros * 6) / 200)
        qtd_rolos_conc = math.ceil(metros / 10)
        qtd_rolos_arame = math.ceil(metros / 50)
        
        adicionar_item_pelo_id("fio_aco", qtd_rolos_fio)
        adicionar_item_pelo_id("concertina_30cm", qtd_rolos_conc)
        adicionar_item_pelo_id("arame_galvanizado", qtd_rolos_arame)

    # 3. Kit Central e Cabeamento
    is_central = str(tem_central).lower() == 'true'
    if is_central:
        adicionar_item_pelo_id("central_sh1800", 1)
        adicionar_item_pelo_id("bateria", 1)
        adicionar_item_pelo_id("sirene", 1)
        adicionar_item_pelo_id("kit_aterramento", 1)
        
        # Injeção dos fios calculados
        adicionar_item_pelo_id("fio_alta_tensao", 1)  # 1 rolo
        adicionar_item_pelo_id("fio_paralelo", 15)    # 15 metros
        adicionar_item_pelo_id("fio_sirene", 2)       # 2 metros
        adicionar_item_pelo_id("fio_aterramento", 20) # 20 metros

    total_materiais = sum(i["quantidade"] * i["preco_unitario"] for i in itens)
    
    return {
        "itens": itens,
        "total_materiais": total_materiais
    }
