from flask import Blueprint, jsonify, render_template, session, request, redirect
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

    receita_total = round(c.fetchone()[0], 2)
    
    # gráfico entradas por hora
    c.execute("""
        SELECT 
        strftime('%H', entrada) as hora,
        COUNT(*) as total
        FROM carros
        WHERE parque_id = ?
        GROUP BY hora
        ORDER BY hora
    """, (parque_id,))

    grafico = c.fetchall()

    horas = []
    totais = []

    for row in grafico:
        horas.append(f"{row['hora']}:00")
        totais.append(row["total"])

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
        receita_total=receita_total,
        horas=horas,
        totais=totais
    )

@admin_park_bp.route("/admin/park/<int:parque_id>/update",methods=["POST"])
@login_required
def update_park(parque_id):

    user_id = session["user_id"]

    conn = db()
    c = conn.cursor()

    # validar acesso
    c.execute("""
        SELECT 1
        FROM admin_parques
        WHERE admin_id = ?
        AND parque_id = ?
    """, (user_id, parque_id))

    if not c.fetchone():
        conn.close()
        return "Acesso negado", 403

    nome = request.form["nome"]
    localizacao = request.form["localizacao"]
    capacidade = int(request.form["capacidade"])

    preco_base = float(request.form["preco_base"])
    preco_min = float(request.form["preco_min"])

    ativo = int(request.form["ativo"])

    c.execute("""
        UPDATE parques
        SET
            nome = ?,
            localizacao = ?,
            capacidade = ?,
            preco_base = ?,
            preco_min = ?,
            ativo = ?
        WHERE id = ?
    """, (
        nome,
        localizacao,
        capacidade,
        preco_base,
        preco_min,
        ativo,
        parque_id
    ))

    conn.commit()
    conn.close()

    return redirect(f"/admin/park/{parque_id}")

@admin_park_bp.route("/admin/park/<int:parque_id>/forcar_saida", methods=["POST"])
@login_required
def forcar_saida(parque_id):
    user_id = session["user_id"]
    dados = request.get_json()
    matricula = dados.get("matricula", "").strip().upper()

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # validar acesso
    c.execute("""
        SELECT 1 FROM admin_parques
        WHERE admin_id = ? AND parque_id = ?
    """, (user_id, parque_id))

    if not c.fetchone():
        conn.close()
        return jsonify({"ok": False, "msg": "Acesso negado"}), 403

    # buscar carro
    c.execute("""
        SELECT * FROM carros
        WHERE matricula = ? AND parque_id = ? AND ativo = 1
        ORDER BY entrada DESC LIMIT 1
    """, (matricula, parque_id))

    carro = c.fetchone()

    if not carro:
        conn.close()
        return jsonify({"ok": False, "msg": "Veículo não encontrado"})

    from datetime import datetime
    agora = datetime.now()
    entrada_dt = datetime.fromisoformat(carro["entrada"])
    tempo_min = int((agora - entrada_dt).total_seconds() / 60)

    # buscar preços do parque
    c.execute("SELECT preco_base, preco_min FROM parques WHERE id = ?", (parque_id,))
    precos = c.fetchone()
    preco = max(precos["preco_base"], tempo_min * precos["preco_min"])

    c.execute("""
        UPDATE carros
        SET saida = ?, ativo = 0, preco = ?, tempo = ?, pago = 1    
        WHERE id = ?
    """, (agora.isoformat(), round(preco, 2), tempo_min, carro["id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": f"Saída forçada — {tempo_min} min — {round(preco,2)}€"
    })
    
@admin_park_bp.route("/admin/park/<int:parque_id>/receita")
@login_required
def receita_periodo(parque_id):

    periodo = request.args.get("periodo", "total")

    conn = db()
    c = conn.cursor()

    filtro = ""

    if periodo == "dia":
        filtro = "AND date(pg.data) = date('now')"

    elif periodo == "semana":
        filtro = "AND pg.data >= datetime('now', '-7 days')"

    elif periodo == "mes":
        filtro = "AND pg.data >= datetime('now', '-30 days')"

    query = f"""
        SELECT COALESCE(SUM(pg.valor), 0)
        FROM pagamentos pg
        JOIN carros c
            ON c.id = pg.carro_id
        WHERE c.parque_id = ?
        {filtro}
    """

    c.execute(query, (parque_id,))

    total = round(c.fetchone()[0], 2)

    conn.close()

    return jsonify({
        "ok": True,
        "total": total
    })

@admin_park_bp.route("/admin/park/<int:parque_id>/receita_chart")
@login_required
def receita_chart(parque_id):

    periodo = request.args.get("periodo", "daily")

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    labels = []
    totals = []

    if periodo == "daily":
        # Last 30 days
        c.execute("""
            SELECT 
                date(pg.data) as data,
                COALESCE(SUM(pg.valor), 0) as total
            FROM pagamentos pg
            JOIN carros c ON c.id = pg.carro_id
            WHERE c.parque_id = ?
            AND pg.data >= datetime('now', '-30 days')
            GROUP BY date(pg.data)
            ORDER BY data
        """, (parque_id,))

        rows = c.fetchall()
        for row in rows:
            labels.append(row['data'])
            totals.append(round(row['total'], 2))

    elif periodo == "monthly":
        # Last 12 months
        c.execute("""
            SELECT 
                strftime('%Y-%m', pg.data) as mes,
                COALESCE(SUM(pg.valor), 0) as total
            FROM pagamentos pg
            JOIN carros c ON c.id = pg.carro_id
            WHERE c.parque_id = ?
            AND pg.data >= datetime('now', '-365 days')
            GROUP BY strftime('%Y-%m', pg.data)
            ORDER BY mes
        """, (parque_id,))

        rows = c.fetchall()
        for row in rows:
            labels.append(row['mes'])
            totals.append(round(row['total'], 2))

    elif periodo == "yearly":
        # All years
        c.execute("""
            SELECT 
                strftime('%Y', pg.data) as ano,
                COALESCE(SUM(pg.valor), 0) as total
            FROM pagamentos pg
            JOIN carros c ON c.id = pg.carro_id
            WHERE c.parque_id = ?
            GROUP BY strftime('%Y', pg.data)
            ORDER BY ano
        """, (parque_id,))

        rows = c.fetchall()
        for row in rows:
            labels.append(row['ano'])
            totals.append(round(row['total'], 2))

    conn.close()

    return jsonify({
        "ok": True,
        "labels": labels,
        "totals": totals
    })