# core/pdf/service_descriptions.py
def get_service_description(service_id: str):
    services = {
        "fence_concertina": {
            "title": "ORÇAMENTO 01 — Cerca elétrica + Concertina (instalação)",
            "description": (
                "Instalação completa de cerca elétrica + concertina, "
                "com montagem, fixação, cabeamento, configuração e testes."
            ),
            "includes": [
                "Central eletrificadora SH1800 (permite controle remoto)",
                "02 (dois) sensores de abertura para portas/janelas",
                "Materiais e mão de obra de instalação",
                "Configuração e testes finais do sistema",
            ],
            "advantages": [
                "Dupla proteção: barreira física + barreira elétrica",
                "Maior poder de inibição contra invasões",
                "Sistema regulado para evitar falsos disparos",
                "Excelente custo-benefício em segurança perimetral",
            ],
        },

        "concertina_linear": {
            "title": "ORÇAMENTO 02 — Concertina linear eletrificada (instalação)",
            "description": (
                "Instalação completa de concertina linear eletrificada, "
                "com montagem, fixação, cabeamento, configuração e testes."
            ),
            "includes": [
                "Central eletrificadora SH1800 (permite controle remoto)",
                "02 (dois) sensores de abertura para portas/janelas",
                "Materiais e mão de obra de instalação",
                "Configuração e testes finais do sistema",
            ],
            "advantages": [
                "Proteção elétrica contínua no topo do muro",
                "Visual mais limpo e instalação padronizada",
                "Sistema testado e regulado para máxima eficiência",
                "Entrega pronta para uso com orientações básicas",
            ],
        },

        "fence": {
            "title": "ORÇAMENTO 03 — Cerca elétrica (instalação)",
            "description": (
                "Instalação completa de cerca elétrica, "
                "com montagem, cabeamento, configuração e testes."
            ),
            "includes": [
                "Central eletrificadora SH1800 (permite controle remoto)",
                "02 (dois) sensores de abertura para portas/janelas",
                "Materiais e mão de obra de instalação",
                "Configuração e testes finais do sistema",
            ],
            "advantages": [
                "Proteção perimetral contínua",
                "Sistema com aterramento adequado",
                "Redução de riscos de invasão",
                "Ótimo custo-benefício em segurança",
            ],
        },
    }

    return services.get(service_id)
