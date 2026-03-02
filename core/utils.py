import re
from datetime import datetime
from typing import Any, Dict, List

# ==========================================
# 1. DINHEIRO (Substitui o antigo money.py)
# ==========================================
def brl(value: float) -> str:
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

# ==========================================
# 2. MATERIAIS (Substitui o antigo materials.py)
# ==========================================
DEFAULT_EXCLUDE_KEYWORDS = [
    "mão de obra", "mao de obra", "taxa base", "instalação", "instalacao",
    "serviço", "servico", "configuração", "configuracao", "teste", "testes", "regulagem"
]

def is_material_item(desc: str, exclude_keywords: List[str] | None = None) -> bool:
    d = (desc or "").lower()
    kws = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS
    return not any(k in d for k in kws)

def build_materials_list(quote: Dict[str, Any], *, exclude_keywords: List[str] | None = None, group_same_desc: bool = True) -> List[Dict[str, Any]]:
    items = quote.get("items", []) or []
    materials = []

    for it in items:
        desc = str(it.get("desc", "")).strip()
        if not desc or not is_material_item(desc, exclude_keywords):
            continue
        materials.append({"desc": desc, "qty": float(it.get("qty", 0))})

    if not group_same_desc:
        return materials

    grouped = {}
    for m in materials:
        grouped[m["desc"]] = grouped.get(m["desc"], 0) + m["qty"]

    result = [{"desc": desc, "qty": int(qty) if qty.is_integer() else qty} for desc, qty in grouped.items()]
    result.sort(key=lambda x: x["desc"].lower())
    return result

# ==========================================
# 3. GERAIS E MATEMÁTICA
# ==========================================
def ceil_div(a: float, b: float) -> int:
    return int((a + b - 1) // b)

def data_br_curta(dt: datetime | None = None) -> str:
    meses = {1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun", 7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"}
    dt = dt or datetime.now()
    return f"{dt.day} de {meses[dt.month]}"

def slug_filename(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[\\/:*?\"<>|]+", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s

def make_pdf_name_multi(cliente: str, dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    cliente_nome = slug_filename(cliente)
    return f"{cliente_nome} - Orçamento - {data_br_curta(dt)}.pdf"
