from db import db
from datetime import datetime

def limpar_reservas():
    conn = db()
    c = conn.cursor()

    agora = datetime.now().isoformat()

    c.execute("""
        UPDATE reservas
        SET ativo = 0
        WHERE expira < ? AND ativo = 1
    """, (agora,))

    conn.commit()
    conn.close()