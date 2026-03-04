from sqlalchemy.orm import Session
from fastapi import HTTPException

# Função auxiliar para buscar preço no banco (Substitui o seu antigo get_price)
def obter_preco_oficial(db: Session, codigo_servico: str):
    from main import Servico # Import local
    item = db.query(Servico).filter(Servico.codigo == codigo_servico).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Falta cadastrar o código '{codigo_servico}' no banco de dados!")
    return item

def calcular_cftv_install(itens_do_pedido: list, db: Session):
    itens_processados = []
    total_materiais = 0.0
    qtd_cameras = 0
    
    # 1. VARRE O PEDIDO PARA DESCOBRIR QUANTAS CÂMERAS O CLIENTE QUER
    for item in itens_do_pedido:
        if "CAM" in item.codigo.upper() or "CAMERA" in item.codigo.upper():
            qtd_cameras += item.quantidade
            
        # Adiciona o item principal que veio do frontend (ex: a Câmera, o Cabo, o DVR)
        servico_real = obter_preco_oficial(db, item.codigo)
        subtotal_item = servico_real.preco_base * item.quantidade
        total_materiais += subtotal_item
        
        itens_processados.append({
            "nome": servico_real.nome,
            "quantidade": item.quantidade,
            "subtotal": subtotal_item
        })

    # ==============================================================
    # 2. A SUA LÓGICA DE CFTV (O "Pulo do Gato" que estava faltando)
    # Se o cliente pediu câmeras, nós calculamos os periféricos automaticamente!
    # ==============================================================
    if qtd_cameras > 0:
        # Lógica: 1 Câmera exige 2 Baluns, 1 P4 Macho e 1 P4 Fêmea
        qtd_baluns = qtd_cameras * 2
        qtd_p4 = qtd_cameras # 1 Macho e 1 Fêmea por câmera
        
        # Busca os preços dos conectores no banco (Você precisa ter esses códigos cadastrados!)
        # Exemplo de códigos fixos que você usava: "cftv_balun", "cftv_p4_macho"
        try:
            balun = obter_preco_oficial(db, "BALUN-01") # Substitua pelo código real do seu banco
            p4_macho = obter_preco_oficial(db, "P4-MACHO")
            p4_femea = obter_preco_oficial(db, "P4-FEMEA")
            
            # Subtotais periféricos
            sub_balun = balun.preco_base * qtd_baluns
            sub_p4_m = p4_macho.preco_base * qtd_p4
            sub_p4_f = p4_femea.preco_base * qtd_p4
            
            total_materiais += (sub_balun + sub_p4_m + sub_p4_f)
            
            # Injeta os conectores invisíveis na lista do PDF
            itens_processados.extend([
                {"nome": f"Balun de Vídeo (Para {qtd_cameras} Câmeras)", "quantidade": qtd_baluns, "subtotal": sub_balun},
                {"nome": f"Conector P4 Macho", "quantidade": qtd_p4, "subtotal": sub_p4_m},
                {"nome": f"Conector P4 Fêmea", "quantidade": qtd_p4, "subtotal": sub_p4_f}
            ])
        except HTTPException:
            # Se você não cadastrou os conectores no banco, ele pula para não quebrar o PDF
            pass

    return {
        "itens_processados": itens_processados,
        "total_materiais": total_materiais
    }
