import re
from datetime import datetime

def ceil_div(a: float, b: float) -> int:
    return int((a + b - 1) // b)

def data_br_curta(dt: datetime | None = None) -> str:
    meses = {
        1: "jan", 2: "fev", 3: "mar", 4: "abr",
        5: "mai", 6: "jun", 7: "jul", 8: "ago",
        9: "set", 10: "out", 11: "nov", 12: "dez",
    }
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
