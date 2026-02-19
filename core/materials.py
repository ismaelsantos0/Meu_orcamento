# core/materials.py
from typing import Any, Dict, List

DEFAULT_EXCLUDE_KEYWORDS = [
    "mão de obra",
    "mao de obra",
    "taxa base",
    "instalação",
    "instalacao",
    "serviço",
    "servico",
    "configuração",
    "configuracao",
    "teste",
    "testes",
    "regulagem",
]


def is_material_item(desc: str, exclude_keywords: List[str] | None = None) -> bool:
    d = (desc or "").lower()
    kws = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS
    return not any(k in d for k in kws)


def build_materials_list(
    quote: Dict[str, Any],
    *,
    exclude_keywords: List[str] | None = None,
    group_same_desc: bool = True,
) -> List[Dict[str, Any]]:
    items = quote.get("items", []) or []
    materials = []

    for it in items:
        desc = str(it.get("desc", "")).strip()
        if not desc:
            continue
        if not is_material_item(desc, exclude_keywords):
            continue

        materials.append({
            "desc": desc,
            "qty": float(it.get("qty", 0)),
        })

    if not group_same_desc:
        return materials

    grouped = {}
    for m in materials:
        grouped[m["desc"]] = grouped.get(m["desc"], 0) + m["qty"]

    result = []
    for desc, qty in grouped.items():
        result.append({
            "desc": desc,
            "qty": int(qty) if qty.is_integer() else qty,
        })

    result.sort(key=lambda x: x["desc"].lower())
    return result


def materials_text_for_whatsapp(
    materials: List[Dict[str, Any]],
    *,
    title: str = "LISTA DE MATERIAIS (COMPRA)",
    header_lines: List[str] | None = None,
) -> str:
    lines = [title]

    if header_lines:
        lines.extend(header_lines)

    lines.append("")
    for m in materials:
        lines.append(f"- {m['desc']} — Qtd: {m['qty']}")

    return "\n".join(lines).strip()
# core/materials.py
from typing import Any, Dict, List

DEFAULT_EXCLUDE_KEYWORDS = [
    "mão de obra",
    "mao de obra",
    "taxa base",
    "instalação",
    "instalacao",
    "serviço",
    "servico",
    "configuração",
    "configuracao",
    "teste",
    "testes",
    "regulagem",
]


def is_material_item(desc: str, exclude_keywords: List[str] | None = None) -> bool:
    d = (desc or "").lower()
    kws = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS
    return not any(k in d for k in kws)


def build_materials_list(
    quote: Dict[str, Any],
    *,
    exclude_keywords: List[str] | None = None,
    group_same_desc: bool = True,
) -> List[Dict[str, Any]]:
    items = quote.get("items", []) or []
    materials = []

    for it in items:
        desc = str(it.get("desc", "")).strip()
        if not desc:
            continue
        if not is_material_item(desc, exclude_keywords):
            continue

        materials.append({
            "desc": desc,
            "qty": float(it.get("qty", 0)),
        })

    if not group_same_desc:
        return materials

    grouped = {}
    for m in materials:
        grouped[m["desc"]] = grouped.get(m["desc"], 0) + m["qty"]

    result = []
    for desc, qty in grouped.items():
        result.append({
            "desc": desc,
            "qty": int(qty) if qty.is_integer() else qty,
        })

    result.sort(key=lambda x: x["desc"].lower())
    return result


def materials_text_for_whatsapp(
    materials: List[Dict[str, Any]],
    *,
    title: str = "LISTA DE MATERIAIS (COMPRA)",
    header_lines: List[str] | None = None,
) -> str:
    lines = [title]

    if header_lines:
        lines.extend(header_lines)

    lines.append("")
    for m in materials:
        lines.append(f"- {m['desc']} — Qtd: {m['qty']}")

    return "\n".join(lines).strip()
