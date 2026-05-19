from flask import Blueprint, request, jsonify
from datetime import datetime
import sqlite3
from .database import db


parking_bp = Blueprint("parking", __name__)

# =========================
# ENTRADA
# =========================
@parking_bp.route("/entrada/<int:parque_id>", methods=["POST"])
def entrada(parque_id):

    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # verificar se já está dentro
    c.execute("""
        SELECT id
        FROM carros
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 1
    """, (matricula, parque_id))

    existe = c.fetchone()

    if existe:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Veículo já está dentro do parque"
        }), 409

    # verificar pagamento pendente
    c.execute("""
        SELECT id
        FROM carros
        WHERE matricula = ?
        AND ativo = 0
        AND pago = 0
        ORDER BY entrada DESC
        LIMIT 1
    """, (matricula,))

    pendente = c.fetchone()

    if pendente:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Pagamento pendente"
        }), 403

    # verificar reserva
    c.execute("""
        SELECT id
        FROM reservas
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 1
    """, (matricula, parque_id))

    reserva = c.fetchone()

    if reserva:
        c.execute("""
            UPDATE reservas
            SET ativo = 0
            WHERE id = ?
        """, (reserva[0],))

    # capacidade do parque
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Parque inválido"
        }), 404

    capacidade = parque[0]

    # ocupados
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    if ocupados >= capacidade:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Parque cheio"
        }), 403

    # registar entrada
    agora = datetime.now().isoformat()

    c.execute("""
        INSERT INTO carros (
            parque_id,
            matricula,
            entrada,
            ativo
        )
        VALUES (?, ?, ?, 1)
    """, (
        parque_id,
        matricula,
        agora
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Entrada autorizada",
        "matricula": matricula,
        "entrada": agora
    })


# =========================
# SAIDA
# =========================
@parking_bp.route("/saida/<int:parque_id>", methods=["POST"])
def saida(parque_id):

    data = request.json
    matricula = data["matricula"]

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # procurar carro ativo
    c.execute("""
        SELECT *
        FROM carros
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 1
        ORDER BY entrada DESC
        LIMIT 1
    """, (matricula, parque_id))

    carro = c.fetchone()

    if not carro:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Veículo não encontrado"
        }), 404

    agora = datetime.now()

    entrada_dt = datetime.fromisoformat(carro["entrada"])

    tempo_min = int(
        (agora - entrada_dt).total_seconds() / 60
    )

    preco = max(1.0, tempo_min * 0.05)

    agora_str = agora.isoformat()

    # fechar registo
    c.execute("""
        UPDATE carros
        SET saida = ?, ativo = 0
        WHERE id = ?
    """, (
        agora_str,
        carro["id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Saída registada",
        "tempo_min": tempo_min,
        "preco": round(preco, 2)
    })


# =========================
# ESTADO REAL
# =========================
@parking_bp.route("/api/estado_real/<int:parque_id>")
def estado_real(parque_id):

    conn = db()
    c = conn.cursor()

    # capacidade
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Parque inválido"
        }), 404

    capacidade = parque[0]

    sensores = [0] * capacidade

    # carros ativos
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    # reservas
    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    reservados = c.fetchone()[0]

    total = ocupados + reservados

    for i in range(min(total, capacidade)):
        sensores[i] = 1

    conn.close()

    return jsonify({
        "ok": True,
        "ocupados": ocupados,
        "reservados": reservados,
        "total": total,
        "sensores": sensores
    })