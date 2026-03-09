import math

def calcular_cerca_completa(metros: float, distancia_haste: float, tipo: str, tem_central: bool, materiais_db: dict):
    itens = []
    
    def adicionar_item_pelo_id(slug: str, quantidade: float, preco_custom=None):
        # Fallbacks genéricos do sistema VERO
        fallbacks = {
            "haste_cerca": {"nome": "Haste de Cerca 1m", "preco": 19.00},
            "fio_aco": {"nome": "Fio de Aço (Rolo 200m)", "preco": 80.00},
            "concertina_30cm": {"nome": "Rolo Concertina 30cm (10m)", "preco": 90.00},
            "concertina_linear": {"nome": "Rolo Concertina Linear (20m)", "preco": 53.00},
            "central_sh1800": {"nome": "Central Eletrificadora", "preco": 310.00},
            "bateria": {"nome": "Bateria 7A", "preco": 83.00},
            "sirene": {"nome": "Sirene", "preco": 2.00},
            "kit_aterramento": {"nome": "Kit Aterramento", "preco": 45.00},
            "arame_galvanizado": {"nome": "Arame Galvanizado (Sustentação)", "preco": 80.00},
            "fio_alta_tensao": {"nome": "Cabo de Alta Tensão (50m)", "preco": 90.00},
            "fio_paralelo": {"nome": "Fio Paralelo (Metro)", "preco": 2.50},
            "fio_sirene": {"nome": "Fio para Sirene (Metro)", "preco": 4.00},
            "fio_aterramento": {"nome": "Fio para Aterramento (Metro)", "preco": 3.00}
        }
        
        item = materiais_db.get(slug, fallbacks.get(slug))
        preco_final = preco_custom if preco_custom is not None else item["preco"]
        
        if item and quantidade > 0:
            itens.append({
                "nome": item["nome"],
                "quantidade": quantidade,
                "preco_unitario": preco_final
            })

    # 1. Cálculo de Hastes
    qtd_hastes = math.ceil(metros / distancia_haste) + 1
    adicionar_item_pelo_id("haste_cerca", qtd_hastes)

    # 2. Lógica de Materiais + Mão de Obra (SaaS VERO Rules)
    tipo_seguro = str(tipo).strip().lower()
    mao_de_obra_total = 0

    if tipo_seguro == "simples":
        qtd_rolos_fio = math.ceil((metros * 6) / 200)
        adicionar_item_pelo_id("fio_aco", qtd_rolos_fio)
        mao_de_obra_total = metros * 10.00
        
    elif tipo_seguro == "concertina_linear":
        qtd_rolos_linear = math.ceil((metros * 6) / 20)
        adicionar_item_pelo_id("concertina_linear", qtd_rolos_linear)
        mao_de_obra_total = metros * 30.00

    elif tipo_seguro == "com_concertina":
        qtd_rolos_fio = math.ceil((metros * 6) / 200)
        qtd_rolos_conc = math.ceil(metros / 10)
        qtd_rolos_arame = math.ceil(metros / 50)
        adicionar_item_pelo_id("fio_aco", qtd_rolos_fio)
        adicionar_item_pelo_id("concertina_30cm", qtd_rolos_conc)
        adicionar_item_pelo_id("arame_galvanizado", qtd_rolos_arame)
        mao_de_obra_total = metros * 25.00

    # 3. Central e Cabeamento
    if str(tem_central).lower() == 'true':
        adicionar_item_pelo_id("central_sh1800", 1)
        adicionar_item_pelo_id("bateria", 1)
        adicionar_item_pelo_id("sirene", 1)
        adicionar_item_pelo_id("kit_aterramento", 1)
        adicionar_item_pelo_id("fio_alta_tensao", 1)
        adicionar_item_pelo_id("fio_paralelo", 15)
        adicionar_item_pelo_id("fio_sirene", 2)
        adicionar_item_pelo_id("fio_aterramento", 20)
        mao_de_obra_total += 150.00

    # Injeta a linha de serviço no carrinho do VERO
    itens.append({
        "nome": f"Mão de Obra: Instalação de {tipo.replace('_', ' ').title()}",
        "quantidade": 1,
        "preco_unitario": mao_de_obra_total
    })

    return {"itens": itens}
