import sqlite3
from flask import Blueprint, request, jsonify, render_template
from .database import db
from .auth import login_required

admin_server_bp = Blueprint("admin_server", __name__)


# =========================
# DASHBOARD SERVER ADMIN
# =========================
@admin_server_bp.route("/admin/server")
@login_required
def admin_server():

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # =========================
    # PARQUES + ADMIN ASSOCIADO
    # =========================

    c.execute("""
        SELECT
            p.id,
            p.nome,
            p.localizacao,
            p.capacidade,
            u.id AS admin_id,
            u.username AS admin_username
        FROM parques p
        LEFT JOIN admin_parques ap
            ON p.id = ap.parque_id
        LEFT JOIN utilizadores u
            ON ap.admin_id = u.id
        ORDER BY p.id
    """)

    parques = c.fetchall()

    # =========================
    # ADMINS + PARQUE ASSOCIADO
    # =========================

    c.execute("""
        SELECT
            u.id,
            u.nome,
            u.username,
            p.id AS parque_id,
            p.nome AS parque_nome
        FROM utilizadores u
        LEFT JOIN admin_parques ap
            ON u.id = ap.admin_id
        LEFT JOIN parques p
            ON ap.parque_id = p.id
        WHERE u.tipo = 'park_admin'
        ORDER BY u.id
    """)

    admins = c.fetchall()

    conn.close()

    return render_template(
        "admin_server.html",
        parques=parques,
        admins=admins
    )


# =========================
# CRIAR PARQUE
# =========================
@admin_server_bp.route("/admin/parques/criar", methods=["POST"])
def criar_parque():

    data = request.json

    nome = data["nome"]
    capacidade = data["capacidade"]
    localizacao = data.get("localizacao", "")

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO parques (
            nome,
            localizacao,
            capacidade
        )
        VALUES (?, ?, ?)
    """, (
        nome,
        localizacao,
        capacidade
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Parque criado"
    })


# =========================
# REMOVER PARQUE
# =========================
@admin_server_bp.route("/admin/parques/remover/<int:parque_id>", methods=["POST"])
def remover_parque(parque_id):

    conn = db()
    c = conn.cursor()

    c.execute("""
        DELETE FROM parques
        WHERE id = ?
    """, (parque_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Parque removido"
    })


# =========================
# CRIAR PARK ADMIN
# =========================
@admin_server_bp.route("/admin/utilizadores/criar", methods=["POST"])
def criar_admin():

    data = request.json

    nome = data.get("nome", "")
    username = data["username"]
    password = data["password"]

    conn = db()
    c = conn.cursor()

    # verificar username
    c.execute("""
        SELECT id
        FROM utilizadores
        WHERE username = ?
    """, (username,))

    existe = c.fetchone()

    if existe:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Username já existe"
        }), 409

    c.execute("""
        INSERT INTO utilizadores (
            nome,
            username,
            password,
            tipo
        )
        VALUES (?, ?, ?, 'park_admin')
    """, (
        nome,
        username,
        password
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Administrador criado"
    })
# =========================
# REMOVER PARK ADMIN
# =========================
@admin_server_bp.route("/admin/utilizadores/remover/<int:admin_id>", methods=["POST"])
def remover_admin(admin_id):

    conn = db()
    c = conn.cursor()

    c.execute("""
        DELETE FROM admin_parques
        WHERE admin_id = ?
    """, (admin_id,))

    c.execute("""
        DELETE FROM utilizadores
        WHERE id = ?
        AND tipo = 'park_admin'
    """, (admin_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True
    })
# =========================
# ASSOCIAR ADMIN A PARQUE
# =========================
@admin_server_bp.route("/admin/assign", methods=["POST"])
def assign_admin():

    data = request.json

    admin_id = data["admin_id"]
    parque_id = data["parque_id"]

    conn = db()
    c = conn.cursor()

    # evitar duplicados
    c.execute("""
        SELECT id
        FROM admin_parques
        WHERE admin_id = ?
        AND parque_id = ?
    """, (
        admin_id,
        parque_id
    ))

    existe = c.fetchone()

    if existe:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Associação já existe"
        }), 409

    c.execute("""
        INSERT INTO admin_parques (
            admin_id,
            parque_id
        )
        VALUES (?, ?)
    """, (
        admin_id,
        parque_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Administrador associado"
    })


# =========================
# DESASSOCIAR ADMIN
# =========================
@admin_server_bp.route("/admin/unassign", methods=["POST"])
def desassociar_admin():

    data = request.json

    admin_id = data["admin_id"]
    parque_id = data["parque_id"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        DELETE FROM admin_parques
        WHERE admin_id = ?
        AND parque_id = ?
    """, (
        admin_id,
        parque_id
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Administrador removido do parque"
    })