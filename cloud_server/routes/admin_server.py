import sqlite3
from flask import Blueprint, request, jsonify, render_template
from .database import db
from .auth import login_required
import secrets
import string

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

    # c.execute("""
    #     SELECT *
    #     FROM parques
    #     ORDER BY nome
    # """)

    # parques = c.fetchall()

    c.execute("""
        SELECT *
        FROM utilizadores
        WHERE tipo='park_admin'
        ORDER BY username
    """)

    admins = c.fetchall()

    c.execute("""
        SELECT
            ap.admin_id,
            ap.parque_id,
            u.username,
            p.nome AS parque_nome
        FROM admin_parques ap
        JOIN utilizadores u
            ON ap.admin_id = u.id
        JOIN parques p
            ON ap.parque_id = p.id
        ORDER BY u.username
    """)

    associacoes = c.fetchall()

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

    # c.execute("""
    #     SELECT
    #         u.id,
    #         u.nome,
    #         u.username,
    #         p.id AS parque_id,
    #         p.nome AS parque_nome
    #     FROM utilizadores u
    #     LEFT JOIN admin_parques ap
    #         ON u.id = ap.admin_id
    #     LEFT JOIN parques p
    #         ON ap.parque_id = p.id
    #     WHERE u.tipo = 'park_admin'
    #     ORDER BY u.id
    # """)

    # admins = c.fetchall()

    c.execute("""
        SELECT *
        FROM tokens
        ORDER BY id DESC
    """)

    tokens = c.fetchall()

    conn.close()

    return render_template(
        "admin_server.html",
        parques=parques,
        admins=admins,
        associacoes=associacoes,
        tokens=tokens
    )


# =========================
# MÉTRICAS
# =========================
@admin_server_bp.route("/admin/metrics")
@login_required
def get_metrics():

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as count FROM parques")
    total_parques = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM utilizadores WHERE tipo='park_admin'")
    total_admins = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM carros WHERE ativo=1")
    carros_estacionados = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM reservas WHERE ativo=1")
    reservas_ativas = c.fetchone()["count"]

    c.execute("SELECT COALESCE(SUM(valor), 0) as total FROM pagamentos")
    receita_total = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as count FROM tokens WHERE usado=1")
    tokens_usados = c.fetchone()["count"]

    c.execute("SELECT COUNT(*) as count FROM tokens WHERE usado=0")
    tokens_disponiveis = c.fetchone()["count"]

    c.execute("""
        SELECT
            p.id,
            p.nome,
            p.capacidade,
            COUNT(c.id) as carros_atuais
        FROM parques p
        LEFT JOIN carros c ON p.id = c.parque_id AND c.ativo=1
        GROUP BY p.id
    """)

    ocupacao_parques = []
    for parque in c.fetchall():
        taxa = (parque["carros_atuais"] / parque["capacidade"] * 100) if parque["capacidade"] > 0 else 0
        ocupacao_parques.append({
            "nome": parque["nome"],
            "ocupacao": round(taxa, 1),
            "carros": parque["carros_atuais"],
            "capacidade": parque["capacidade"]
        })

    conn.close()

    return jsonify({
        "total_parques": total_parques,
        "total_admins": total_admins,
        "carros_estacionados": carros_estacionados,
        "reservas_ativas": reservas_ativas,
        "receita_total": round(receita_total, 2),
        "tokens_usados": tokens_usados,
        "tokens_disponiveis": tokens_disponiveis,
        "ocupacao_parques": ocupacao_parques
    })


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

# =========================
# GERAR TOKENS
# =========================
def gerar_token(tamanho=12):

    chars = string.ascii_uppercase + string.digits

    return ''.join(
        secrets.choice(chars)
        for _ in range(tamanho)
    )

# =========================
# GERAR TOKENS
# =========================
@admin_server_bp.route("/admin/tokens/criar", methods=["POST"])
@login_required
def criar_token():

    data = request.json

    max_parques = int(data.get("max_parques", 1))

    token = gerar_token()

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO tokens
        (
            token,
            criado_em,
            max_parques
        )
        VALUES (?, datetime('now'), ?)
    """, (
        token,
        max_parques
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "token": token
    })

# =========================
# CONSUMIR TOKENS
# =========================

@admin_server_bp.route("/register")
def register_page():

    return render_template("register.html")

@admin_server_bp.route("/register", methods=["POST"])
def register():

    data = request.json

    token = data["token"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM tokens
        WHERE token = ?
        AND usado = 0
    """, (token,))

    token_row = c.fetchone()

    if not token_row:

        return jsonify({
            "ok": False,
            "msg": "Token inválido"
        })

    parques = data["parques"]

    if len(parques) > token_row["max_parques"]:

        return jsonify({
            "ok": False,
            "msg": "Número máximo de parques excedido"
        })

    c.execute("""
        INSERT INTO utilizadores
        (
            nome,
            username,
            password,
            tipo
        )
        VALUES (?, ?, ?, ?)
    """, (
        data["nome"],
        data["username"],
        data["password"],
        "park_admin"
    ))

    admin_id = c.lastrowid

    for parque in parques:

        c.execute("""
            INSERT INTO parques
            (
                nome,
                localizacao,
                capacidade
            )
            VALUES (?, ?, ?)
        """, (
            parque["nome"],
            parque["localizacao"],
            parque["capacidade"]
        ))

        parque_id = c.lastrowid

        c.execute("""
            INSERT INTO admin_parques
            (
                admin_id,
                parque_id
            )
            VALUES (?, ?)
        """, (
            admin_id,
            parque_id
        ))

    c.execute("""
        UPDATE tokens
        SET usado = 1,
            usado_em = datetime('now')
        WHERE id = ?
    """, (token_row["id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True
    })

# QUANTIDADE DE PARQUES PERMITIDO
@admin_server_bp.route("/token-info/<token>")
def token_info(token):

    conn = db()
    c = conn.cursor()

    c.execute("""
        SELECT
            max_parques,
            usado
        FROM tokens
        WHERE token = ?
    """, (token,))

    row = c.fetchone()

    conn.close()

    if not row:
        return jsonify({
            "ok": False
        })

    if row["usado"]:
        return jsonify({
            "ok": False
        })

    return jsonify({
        "ok": True,
        "max_parques": row["max_parques"]
    })