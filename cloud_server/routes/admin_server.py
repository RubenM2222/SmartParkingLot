import sqlite3
from flask import Blueprint, request, jsonify, render_template
from .database import db

admin_server_bp = Blueprint("admin_server", __name__)


# =========================
# DASHBOARD SERVER ADMIN
# =========================
@admin_server_bp.route("/admin/server")
def admin_server():

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # parques
    c.execute("""
        SELECT *
        FROM parques
    """)

    parques = c.fetchall()

    # admins
    c.execute("""
        SELECT *
        FROM utilizadores
        WHERE tipo = 'park_admin'
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