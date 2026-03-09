import math

def calcular_cerca_completa(metros: float, distancia_haste: float, tipo: str, tem_central: bool, precos_db: dict):
    itens = []
    
    # 1. Cálculo de Hastes
    qtd_hastes = math.ceil(metros / distancia_haste) + 1
    itens.append({"nome": "Haste de Cerca", "quantidade": qtd_hastes, "preco_unitario": precos_db.get("haste_cerca", 0.0)})

    # 2. Lógica do Tipo de Cerca
    if tipo == "simples":
        itens.append({"nome": "Fio de Aço (Rolo)", "quantidade": 1, "preco_unitario": precos_db.get("fio_aco", 0.0)})
        
    elif tipo == "com_concertina":
        qtd_rolos = math.ceil(metros / 10)
        itens.append({"nome": "Rolo Concertina 30cm (10m)", "quantidade": qtd_rolos, "preco_unitario": precos_db.get("concertina_30cm", 0.0)})
        
    elif tipo == "concertina_linear":
        qtd_rolos = math.ceil((metros * 6) / 20)
        itens.append({"nome": "Rolo Concertina Linear (20m - 6 fios)", "quantidade": qtd_rolos, "preco_unitario": precos_db.get("concertina_linear", 0.0)})

    # 3. Kit Central
    if tem_central:
        itens.append({"nome": "Central SH1800", "quantidade": 1, "preco_unitario": precos_db.get("central_sh1800", 0.0)})
        itens.append({"nome": "Bateria 7A", "quantidade": 1, "preco_unitario": precos_db.get("bateria", 0.0)})
        itens.append({"nome": "Sirene", "quantidade": 1, "preco_unitario": precos_db.get("sirene", 0.0)})

    total_materiais = sum(i["quantidade"] * i["preco_unitario"] for i in itens)
    
    return {
        "itens": itens,
        "total_materiais": total_materiais
    }
