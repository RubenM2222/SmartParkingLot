from flask import Blueprint, render_template, session
import sqlite3
from .database import db
from .auth import login_required

admin_park_bp = Blueprint("admin_park", __name__)

@admin_park_bp.route("/admin/park")
def admin_park():

    user_id = session["user_id"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT p.*
        FROM parques p
        JOIN admin_parques ap
        ON p.id = ap.parque_id
        WHERE ap.admin_id = ?
    """, (user_id,))

    parques = c.fetchall()

    conn.close()

    return render_template(
        "admin_park.html",
        parques=parques
    )

@admin_park_bp.route("/admin/park/<int:parque_id>")
def park_detail(parque_id):

    user_id = session["user_id"]

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # validar acesso
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

    # info parque
    c.execute("""
        SELECT *
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    # carros ativos
    c.execute("""
        SELECT *
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
        ORDER BY entrada DESC
    """, (parque_id,))

    carros = c.fetchall()

    # reservas
    c.execute("""
        SELECT *
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    reservas = c.fetchall()

    # ocupados
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    # capacidade
    capacidade = parque["capacidade"]

    livres = capacidade - ocupados

    conn.close()

    return render_template(
        "park_detail.html",
        parque=parque,
        carros=carros,
        reservas=reservas,
        ocupados=ocupados,
        livres=livres
    )