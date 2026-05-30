import threading
import time
from routes.database import db


def limpar_reservas_expiradas():

    conn = db()
    c = conn.cursor()
    
    # DECOMMENT FOR DEBUG
    #c.execute("SELECT datetime('now')")
    #print("NOW =", c.fetchone()[0])

    c.execute("""
        UPDATE reservas
        SET ativo = 0
        WHERE ativo = 1
        AND expira < datetime('now')
    """)

    #c.execute("""
    #    SELECT id, matricula, expira, ativo
    #    FROM reservas
    #""")

    #for row in c.fetchall():
    #    print(dict(row))
    
    conn.commit()
    conn.close()


def limpeza_automatica():

    while True:

        try:
            # print("A verificar reservas expiradas...")
            limpar_reservas_expiradas()
        except Exception as e:
            print("Erro na limpeza automática:", e)

        time.sleep(60)