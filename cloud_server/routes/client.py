from flask import Blueprint, render_template, request, jsonify
from .database import db
import sqlite3
from datetime import datetime, timedelta

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
        parques=parques,
    )

# PARA fazer reservas
@client_bp.route("/reservar", methods=["POST"])
def reservar():

    dados = request.get_json()
    print("DADOS:", dados)

    matricula = dados.get("matricula", "").strip().upper()
    parque_id = dados.get("parque_id")

    if not matricula:
        return jsonify({
            "ok": False,
            "msg": "Matrícula inválida"
        })

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # remover reservas expiradas
    c.execute("""
        UPDATE reservas
        SET ativo = 0
        WHERE ativo = 1
        AND datetime(expira) < datetime('now', 'localtime')
    """)

    # verificar parque
    c.execute("""
        SELECT capacidade, ativo
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Parque não encontrado"
        })

    if parque["ativo"] == 0:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Parque encerrado"
        })

    capacidade = parque["capacidade"]

    # carros dentro do parque
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    # reservas válidas
    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
        AND datetime(expira) > datetime('now', 'localtime')
    """, (parque_id,))

    reservados = c.fetchone()[0]

    livres = capacidade - ocupados - reservados

    if livres <= 0:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Sem lugares disponíveis"
        })

    # verificar se já existe reserva ativa para a matrícula
    c.execute("""
        SELECT id
        FROM reservas
        WHERE matricula = ?
        AND ativo = 1
        AND datetime(expira) > datetime('now', 'localtime')
    """, (matricula,))

    if c.fetchone():
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Já existe uma reserva ativa"
        })

    agora = datetime.now()
    expira = agora + timedelta(minutes=15)

    c.execute("""
        INSERT INTO reservas
        (
            parque_id,
            matricula,
            inicio,
            expira,
            ativo
        )
        VALUES (?, ?, ?, ?, 1)
    """, (
        parque_id,
        matricula,
        agora.isoformat(" "),
        expira.isoformat(" ")
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": f"Reserva criada até {expira.strftime('%H:%M')}"
    })

@client_bp.route("/estado/<int:parque_id>")
def estado(parque_id):

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # limpar reservas expiradas
    c.execute("""
        UPDATE reservas
        SET ativo = 0
        WHERE ativo = 1
        AND datetime(expira) < datetime('now', 'localtime')
    """)
    
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()
        return jsonify({"erro": "Parque não encontrado"}), 404

    capacidade = parque["capacidade"]

    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
        AND datetime(expira) > datetime('now', 'localtime')
    """, (parque_id,))

    reservados = c.fetchone()[0]

    livres = max(0, capacidade - ocupados - reservados)

    conn.commit()
    conn.close()

    return jsonify({
        "livres": livres,
        "ocupados": ocupados,
        "reservados": reservados
    })
    
@client_bp.route("/terminal")
def terminal():
    return render_template("terminal.html")