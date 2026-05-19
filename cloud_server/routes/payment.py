from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from .database import db

payment_bp = Blueprint("payment", __name__)


# =========================
# PAGINA PAGAMENTO
# =========================
@payment_bp.route("/payment/<int:parque_id>")
def payment(parque_id):

    matricula = request.args.get("matricula")

    if not matricula:
        return render_template(
            "payment.html",
            vazio=True
        )

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # procurar ultimo registo fechado e não pago
    c.execute("""
        SELECT *
        FROM carros
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 0
        AND pago = 0
        ORDER BY entrada DESC
        LIMIT 1
    """, (
        matricula,
        parque_id
    ))

    carro = c.fetchone()

    if not carro:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Nenhum pagamento pendente"
        }), 404

    # calcular duração
    entrada_dt = datetime.fromisoformat(
        carro["entrada"]
    )

    saida_dt = datetime.fromisoformat(
        carro["saida"]
    )

    tempo_min = int(
        (saida_dt - entrada_dt).total_seconds() / 60
    )

    # calcular preço
    preco = max(1.0, tempo_min * 0.05)

    # formatar duração
    horas = tempo_min // 60
    minutos = tempo_min % 60

    if horas > 0:
        duracao = f"{horas}h {minutos}m"
    else:
        duracao = f"{minutos} min"

    conn.close()

    return render_template(
        "payment.html",
        matricula=carro["matricula"],
        parque_id=parque_id,
        entrada=carro["entrada"],
        saida=carro["saida"],
        duracao=duracao,
        preco=f"{preco:.2f}",
        carro_id=carro["id"]
    )


# =========================
# CONFIRMAR PAGAMENTO
# =========================
@payment_bp.route("/payment/confirm/<int:carro_id>", methods=["POST"])
def confirmar_pagamento(carro_id):

    conn = db()
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    # verificar registo
    c.execute("""
        SELECT *
        FROM carros
        WHERE id = ?
    """, (carro_id,))

    carro = c.fetchone()

    if not carro:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Registo não encontrado"
        }), 404

    if carro["pago"] == 1:
        conn.close()

        return jsonify({
            "ok": False,
            "msg": "Pagamento já efetuado"
        }), 409

    agora = datetime.now().isoformat()

    # marcar pago
    c.execute("""
        UPDATE carros
        SET pago = 1
        WHERE id = ?
    """, (carro_id,))

    # guardar histórico pagamento
    c.execute("""
        INSERT INTO pagamentos (
            carro_id,
            valor,
            metodo,
            data
        )
        VALUES (?, ?, ?, ?)
    """, (
        carro_id,
        carro["preco"],
        "web",
        agora
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Pagamento confirmado",
        "carro_id": carro_id,
        "data_pagamento": agora
    })