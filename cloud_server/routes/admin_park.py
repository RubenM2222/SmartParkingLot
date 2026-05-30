from flask import Blueprint, render_template, session
import sqlite3
from .database import db
from .auth import login_required

admin_park_bp = Blueprint("admin_park", __name__)


# ==================================================
# DASHBOARD DOS PARQUES DO ADMIN
# ==================================================

@admin_park_bp.route("/admin/park")
@login_required
def admin_park():

    user_id = session["user_id"]

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # parques associados ao admin
    c.execute("""
        SELECT p.*
        FROM parques p
        JOIN admin_parques ap
            ON p.id = ap.parque_id
        WHERE ap.admin_id = ?
        ORDER BY p.nome
    """, (user_id,))

    parques = c.fetchall()

    total_parques = len(parques)
    total_capacidade = 0
    total_ocupados = 0
    total_reservas = 0

    for parque in parques:

        total_capacidade += parque["capacidade"]

        c.execute("""
            SELECT COUNT(*)
            FROM carros
            WHERE parque_id = ?
            AND ativo = 1
        """, (parque["id"],))

        total_ocupados += c.fetchone()[0]

        c.execute("""
            SELECT COUNT(*)
            FROM reservas
            WHERE parque_id = ?
            AND ativo = 1
        """, (parque["id"],))

        total_reservas += c.fetchone()[0]

    conn.close()

    return render_template(
        "admin_park.html",
        parques=parques,
        total_parques=total_parques,
        total_capacidade=total_capacidade,
        total_ocupados=total_ocupados,
        total_reservas=total_reservas
    )


# ==================================================
# GESTÃO DE UM PARQUE
# ==================================================

@admin_park_bp.route("/admin/park/<int:parque_id>")
@login_required
def park_detail(parque_id):

    user_id = session["user_id"]

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # validar acesso ao parque
    c.execute("""
        SELECT 1
        FROM admin_parques
        WHERE admin_id = ?
        AND parque_id = ?
    """, (user_id, parque_id))

    acesso = c.fetchone()

    if not acesso:
        conn.close()
        return "Acesso negado", 403

    # dados do parque
    c.execute("""
        SELECT *
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()
        return "Parque não encontrado", 404

    # carros atualmente no parque
    c.execute("""
        SELECT *
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
        ORDER BY entrada DESC
    """, (parque_id,))

    carros = c.fetchall()

    # reservas ativas
    c.execute("""
        SELECT *
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
        ORDER BY inicio DESC
    """, (parque_id,))

    reservas = c.fetchall()

    # histórico (últimos veículos que saíram)
    c.execute("""
        SELECT *
        FROM carros
        WHERE parque_id = ?
        AND ativo = 0
        ORDER BY saida DESC
        LIMIT 20
    """, (parque_id,))

    historico = c.fetchall()

    # ocupados
    ocupados = len(carros)

    # capacidade
    capacidade = parque["capacidade"]

    # livres
    livres = capacidade - ocupados

    # reservas
    reservados = len(reservas)

    # taxa ocupação
    taxa_ocupacao = 0

    if capacidade > 0:
        taxa_ocupacao = round((ocupados / capacidade) * 100)

    # receita total
    c.execute("""
        SELECT COALESCE(SUM(pg.valor), 0)
        FROM pagamentos pg
        JOIN carros c
            ON c.id = pg.carro_id
        WHERE c.parque_id = ?
    """, (parque_id,))

    receita_total = c.fetchone()[0]

    conn.close()

    return render_template(
        "park_manage.html",
        parque=parque,
        carros=carros,
        reservas=reservas,
        historico=historico,
        ocupados=ocupados,
        livres=livres,
        reservados=reservados,
        taxa_ocupacao=taxa_ocupacao,
        receita_total=receita_total
    )