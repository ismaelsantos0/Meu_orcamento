import os
import sqlite3

DB_PATH = "data/db.sqlite"


def get_conn():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS precos (
            chave TEXT PRIMARY KEY,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL
        )
        """
    )
    return conn


def get_price(conn, key: str, default: float = 0.0) -> float:
    cur = conn.execute("SELECT valor FROM precos WHERE chave=?", (key,))
    row = cur.fetchone()
    return float(row[0]) if row else float(default)


def set_price(conn, key: str, desc: str, value: float) -> None:
    conn.execute(
        """
        INSERT INTO precos (chave, descricao, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE
        SET descricao=excluded.descricao, valor=excluded.valor
        """,
        (key, desc, float(value)),
    )
    conn.commit()


def list_prices(conn):
    cur = conn.execute("SELECT chave, descricao, valor FROM precos ORDER BY chave")
    return cur.fetchall()


def save_prices_bulk(conn, rows):
    # rows: list[(key, desc, value)]
    conn.executemany(
        """
        INSERT INTO precos (chave, descricao, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(chave) DO UPDATE
        SET descricao=excluded.descricao, valor=excluded.valor
        """,
        [(k, d, float(v)) for (k, d, v) in rows],
    )
    conn.commit()


def ensure_seed(conn):
    seeds = [
        # Materiais (cerca)
        ("haste_reta", "Haste de cerca (reta)", 19.0),
        ("haste_canto", "Haste de canto", 50.0),
        ("fio_aco_200m", "Fio de aço 200m", 80.0),
        ("central_sh1800", "Central SH1800", 310.0),
        ("bateria", "Bateria", 83.0),
        ("sirene", "Sirene", 2.0),
        ("concertina_10m", "Concertina 30cm (10m)", 90.0),
        ("concertina_linear_20m", "Concertina linear (20m)", 53.0),

        # Complementos
        ("kit_isoladores", "Kit isoladores (100 un)", 19.90),
        ("cabo_alta_50m", "Cabo de alta isolação (50m)", 75.0),
        ("kit_placas", "Placas de aviso (kit)", 19.0),
        ("kit_aterramento", "Kit aterramento", 165.0),

        # Mão de obra proporcional (base + R$/m)
        ("mao_cerca_base", "Mão de obra cerca (taxa base)", 250.0),
        ("mao_cerca_por_m", "Mão de obra cerca (R$/metro)", 18.0),
        ("mao_concertina_base", "Mão de obra concertina (taxa base)", 150.0),
        ("mao_concertina_por_m", "Mão de obra concertina (R$/metro)", 8.0),
        ("mao_linear_base", "Mão de obra concertina linear (taxa base)", 200.0),
        ("mao_linear_por_m", "Mão de obra concertina linear (R$/metro)", 10.0),

        # CFTV (mão de obra)
        ("mao_cftv_dvr", "Mão de obra CFTV (instalação do DVR)", 200.0),
        ("mao_cftv_por_camera_inst", "Mão de obra CFTV (instalação por câmera)", 120.0),
        ("mao_cftv_por_camera_defeito", "Mão de obra CFTV (manutenção por câmera com defeito)", 80.0),

        # Outros
        ("mao_motor_inst", "Mão de obra Motor (instalação)", 0.0),
        ("mao_motor_man", "Mão de obra Motor (manutenção)", 0.0),
        ("mao_cerca_man", "Mão de obra Cerca (manutenção)", 0.0),
    ]

    for k, d, v in seeds:
        cur = conn.execute("SELECT 1 FROM precos WHERE chave=?", (k,))
        if not cur.fetchone():
            set_price(conn, k, d, v)
