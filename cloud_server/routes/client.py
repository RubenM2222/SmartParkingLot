from flask import Blueprint, render_template
from .database import db
import sqlite3

client_bp = Blueprint("client", __name__)


# =========================
# PAGINA CLIENTE
# =========================
@client_bp.route("/")
def home():

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # obter todos os parques
    c.execute("""
        SELECT *
        FROM parques
    """)

    parques = c.fetchall()

    conn.close()

    return render_template(
        "home.html",
        parques=parques
    )

@client_bp.route("/parque/<int:parque_id>")
def cliente(parque_id):


    conn = db()
    c = conn.cursor()

    # obter parque
    c.execute("""
        SELECT *
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()
        return "Parque não encontrado", 404

    capacidade = parque["capacidade"]

    # carros ativos
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    # reservas ativas
    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    reservados = c.fetchone()[0]

    livres = capacidade - ocupados - reservados

    if livres < 0:
        livres = 0

    conn.close()

    return render_template(
        "cliente.html",
        parque=parque,
        livres=livres,
        ocupados=ocupados,
        reservados=reservados,
        parque_id=parque_id
    )


# =========================
# PAINEL GERAL
# =========================
@client_bp.route("/painel")
def painel():

    conn = db()
    c = conn.cursor()

    # total capacidade
    c.execute("""
        SELECT SUM(capacidade)
        FROM parques
    """)

    capacidade_total = c.fetchone()[0] or 0

    # ocupados
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE ativo = 1
    """)

    ocupados = c.fetchone()[0]

    # reservas
    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE ativo = 1
    """)

    reservados = c.fetchone()[0]

    livres = capacidade_total - ocupados - reservados

    # lista parques
    c.execute("""
        SELECT *
        FROM parques
    """)

    parques = c.fetchall()

    conn.close()

    return render_template(
        "painel.html",
        livres=livres,
        ocupados=ocupados,
        reservados=reservados,
        parques=parques
    )