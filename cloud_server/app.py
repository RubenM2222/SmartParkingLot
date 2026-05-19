from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = "123"
#app.secret_key = os.urandom(24)
#app.secret_key = os.environ.get("SECRET_KEY")

TOTAL_LUGARES = 10
sensor_estado = [0] * TOTAL_LUGARES

def db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS utilizadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    ''')
    # tipo server_admin,park_admin

    c.execute('''
    CREATE TABLE IF NOT EXISTS parques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        localizacao TEXT,
        capacidade INTEGER NOT NULL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS admin_parques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER NOT NULL,
        parque_id INTEGER NOT NULL,

        FOREIGN KEY(admin_id) REFERENCES utilizadores(id),
        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    # c.execute('''
    # CREATE TABLE IF NOT EXISTS carros (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     matricula TEXT,
    #     entrada TEXT,
    #     saida TEXT,
    #     preco REAL,
    #     tempo INTEGER,
    #     ativo INTEGER,
    #     pago TEXT
    # )
    # ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS carros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parque_id INTEGER NOT NULL,

        matricula TEXT NOT NULL,

        entrada TEXT NOT NULL,
        saida TEXT,

        preco REAL DEFAULT 0,
        tempo INTEGER DEFAULT 0,

        ativo INTEGER DEFAULT 1,
        pago INTEGER DEFAULT 0,

        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    # c.execute('''
    # CREATE TABLE IF NOT EXISTS reservas (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     matricula TEXT,
    #     inicio TEXT,
    #     expira TEXT,
    #     ativo INTEGER
    # )
    # ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parque_id INTEGER NOT NULL,

        matricula TEXT NOT NULL,

        inicio TEXT NOT NULL,
        expira TEXT NOT NULL,

        ativo INTEGER DEFAULT 1,

        FOREIGN KEY(parque_id) REFERENCES parques(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        carro_id INTEGER NOT NULL,

        valor REAL NOT NULL,
        metodo TEXT,
        data TEXT NOT NULL,

        FOREIGN KEY(carro_id) REFERENCES carros(id)
    )
    ''')
    c.execute('''
            INSERT INTO utilizadores (nome, username, password, tipo)
            VALUES (?, ?, ?, ?)
        ''', ("Ben", "AdminS", "123", 'server_admin'))
    # INDEXs
    # carros
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_matricula
    ON carros(matricula)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_parque
    ON carros(parque_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_carros_ativo
    ON carros(ativo)
    ''')

    # reservas
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_reservas_parque
    ON reservas(parque_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_reservas_matricula
    ON reservas(matricula)
    ''')

    # admin_parques
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_admin_parques_admin
    ON admin_parques(admin_id)
    ''')

    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_admin_parques_parque
    ON admin_parques(parque_id)
    ''')

    # utilizadores
    c.execute('''
    CREATE INDEX IF NOT EXISTS idx_utilizadores_username
    ON utilizadores(username)
    ''')

    conn.commit()
    conn.close()

init()

@app.route("/parque/<int:parque_id>")
def cliente(parque_id):

    conn = db()
    c = conn.cursor()

    # capacidade do parque
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    if not parque:
        conn.close()
        return "Parque não encontrado", 404

    capacidade = parque[0]

    # ocupados
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

    livres = capacidade - ocupados - reservados

    if livres < 0:
        livres = 0

    conn.close()

    return render_template(
        "cliente.html",
        livres=livres,
        ocupados=ocupados,
        reservados=reservados,
        parque_id=parque_id
    )

@app.route("/painel")
def painel():
    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
    reservados = c.fetchone()[0]

    livres = TOTAL_LUGARES - ocupados - reservados

    conn.close()

    return render_template("painel.html",
                           livres=livres,
                           ocupados=ocupados,
                           reservados=reservados)

@app.route("/sensor", methods=["POST"])
def sensor():
    global sensor_estado

    data = request.json
    sensores = data["sensores"]

    sensor_estado = sensores

    ocupados = sum(sensores)
    livres = TOTAL_LUGARES - ocupados

    return jsonify({
        "ok": True,
        "estado": sensor_estado
    })
    #return jsonify({
    #    "ok": True,
    #    "ocupados": ocupados,
    #    "livres": livres,
    #    "raw": sensores
    #})

@app.route("/api/sensores")
def get_sensores():
    return jsonify({
        "estado": sensor_estado
    })

@app.route("/api/estado_real")
def estado_real():
    conn = db()
    c = conn.cursor()

    sensores = [0] * TOTAL_LUGARES

    # carros ocupam lugares
    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    # reservas também contam como ocupação virtual
    c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
    reservados = c.fetchone()[0]

    total_ocupados = ocupados + reservados

    for i in range(min(total_ocupados, TOTAL_LUGARES)):
        sensores[i] = 1

    conn.close()

    return jsonify({
        "sensores": sensores,
        "ocupados": total_ocupados
    })

@app.route("/entrada/<int:parque_id>", methods=["POST"])
def entrada(parque_id):

    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # 1. VERIFICAR SE JÁ ESTÁ DENTRO DO MESMO PARQUE
    c.execute("""
        SELECT id FROM carros 
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

    # verificar reserva ativa
    c.execute("""
        SELECT id FROM reservas
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 1
    """, (matricula, parque_id))

    reserva = c.fetchone()

    if reserva:
        # consumir reserva apenas deste parque
        c.execute("""
            UPDATE reservas
            SET ativo = 0
            WHERE id = ?
        """, (reserva[0],))

    # 3. VERIFICAR CAPACIDADE DO PARQUE
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Parque inválido"
        }), 404

    capacidade = row[0]

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

    # 4. REGISTAR ENTRADA
    agora = datetime.now().isoformat()

    c.execute("""
        INSERT INTO carros (
            parque_id,
            matricula,
            entrada,
            ativo
        )
        VALUES (?, ?, ?, 1)
    """, (parque_id, matricula, agora))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Entrada autorizada",
        "parque_id": parque_id,
        "matricula": matricula,
        "entrada": agora
    })

@app.route("/saida/<int:parque_id>", methods=["POST"])
def saida(parque_id):

    data = request.json
    matricula = data["matricula"]

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. procurar carro ativo NO PARQUE
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
            "msg": "Veículo não está neste parque"
        }), 404

    # 2. calcular tempo
    agora = datetime.now()

    entrada_dt = datetime.strptime(
        carro["entrada"],
        "%Y-%m-%dT%H:%M:%S"
    )

    tempo_min = int((agora - entrada_dt).total_seconds() / 60)

    # 3. calcular preço (regra atual)
    preco = max(1, tempo_min * 0.05)

    agora_str = agora.isoformat()

    # 4. fechar registo corretamente
    c.execute("""
        UPDATE carros
        SET saida=?, ativo=0
        WHERE matricula=? AND ativo=1
    """, (agora_str, matricula))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Saída registada",
        "parque_id": parque_id,
        "matricula": matricula,
        "tempo_min": tempo_min,
        "preco": round(preco, 2)
    })

@app.route("/reservar/<int:parque_id>", methods=["POST"])
def reservar(parque_id):

    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # 1. verificar reserva ativa no MESMO parque
    c.execute("""
        SELECT id   
        FROM reservas
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 1
    """, (matricula, parque_id))

    if c.fetchone():
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Já tens uma reserva ativa neste parque"
        })

    # 2. obter capacidade do parque
    c.execute("""
        SELECT capacidade
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Parque inválido"
        }), 404

    capacidade = row[0]

    # 3. contar ocupados neste parque
    c.execute("""
        SELECT COUNT(*)
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    ocupados = c.fetchone()[0]

    # 4. contar reservas neste parque
    c.execute("""
        SELECT COUNT(*)
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    reservados = c.fetchone()[0]

    if ocupados + reservados >= capacidade:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Sem vagas disponíveis"
        }), 409

    # 5. criar reserva
    agora = datetime.now()
    expira = agora + timedelta(minutes=2)

    c.execute("""
        INSERT INTO reservas (
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
        agora.isoformat(),
        expira.isoformat()
    ))

    conn.commit()
    conn.close()

    # limpar expiradas
    limpar_reservas()

    return jsonify({
        "ok": True,
        "msg": "Reserva criada (2 min)",
        "parque_id": parque_id,
        "expira": expira.isoformat()
    })

@app.route("/payment/<int:parque_id>")
def payment(parque_id):

    matricula = request.args.get("matricula")

    if not matricula:
        return render_template("payment.html", vazio=True)

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. procurar último registo fechado e não pago neste parque
    c.execute("""
        SELECT *
        FROM carros
        WHERE matricula = ?
        AND parque_id = ?
        AND ativo = 0
        AND pago = 0
        ORDER BY entrada DESC
        LIMIT 1
    """, (matricula, parque_id))

    carro = c.fetchone()

    if not carro:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Nenhum pagamento pendente encontrado"
        }), 404

    # 2. calcular tempo (garantir consistência com saída)
    entrada_dt = datetime.strptime(
        carro["entrada"],
        "%Y-%m-%dT%H:%M:%S"
    )

    saida_dt = datetime.strptime(
        carro["saida"],
        "%Y-%m-%dT%H:%M:%S"
    )

    tempo_min = int((saida_dt - entrada_dt).total_seconds() / 60)

    # 3. preço (mesma regra da saída)
    preco = max(1.0, tempo_min * 0.05)

    # 4. duração formatada
    horas = tempo_min // 60
    minutos = tempo_min % 60
    duracao_formatada = f"{horas}h {minutos}m" if horas > 0 else f"{minutos} min"

    conn.close()

    return render_template(
        "payment.html",
        matricula=carro["matricula"],
        parque_id=parque_id,
        entrada=carro["entrada"],
        saida=carro["saida"],
        duracao=duracao_formatada,
        preco=f"{preco:.2f}",
        carro_id=carro["id"]
    )

@app.route("/payment/confirm/<int:carro_id>", methods=["POST"])
def confirmar_pagamento(carro_id):

    conn = db()
    c = conn.cursor()

    # 1. verificar se existe e não está pago
    c.execute("""
        SELECT id, pago
        FROM carros
        WHERE id = ?
    """, (carro_id,))

    carro = c.fetchone()

    if not carro:
        conn.close()
        return jsonify({"ok": False, "msg": "Registo não encontrado"}), 404

    if carro["pago"] == 1:
        conn.close()
        return jsonify({"ok": False, "msg": "Já foi pago"}), 409

    agora_pagamento = datetime.now().isoformat()

    # 2. marcar como pago
    c.execute("""
        UPDATE carros
        SET pago = 1
        WHERE id = ?
    """, (carro_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Pagamento confirmado",
        "carro_id": carro_id,
        "data_pagamento": agora_pagamento
    })

# Login & administracao

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():

    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"ok": False, "msg": "Dados em falta"}), 400

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM utilizadores
        WHERE username = ?
    """, (username,))

    user = c.fetchone()

    if not user:
        conn.close()
        return jsonify({"ok": False, "msg": "Utilizador não existe"}), 404

    # versão simples (depois podemos melhorar com hash)
    if user["password"] != password:
        conn.close()
        return jsonify({"ok": False, "msg": "Password incorreta"}), 401

    # guardar sessão
    session["user_id"] = user["id"]
    session["tipo"] = user["tipo"]

    conn.close()

    return jsonify({
        "ok": True,
        "msg": "Login efetuado",
        "tipo": user["tipo"]
    })

def login_required_admin():
    if "user_id" not in session:
        return False
    return True

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            if "user_id" not in session:
                return redirect("/login")

            if session.get("tipo") != role:
                return "Acesso negado", 403

            return f(*args, **kwargs)

        return decorated_function
    return wrapper

@app.route("/admin/server")
@role_required("server_admin")
def admin_server():

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # todos os parques
    c.execute("""
        SELECT * FROM parques
    """)
    parques = c.fetchall()

    # todos os admins de parque
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

@app.route("/admin/park")
@role_required("park_admin")
# def dashboard():
#     password = request.args.get("key")
#     if password != "admin123":
#         return "Acesso negado"
#     # http://IP:5000/admin?key=admin123
#     conn = db()
#     c = conn.cursor()
#     # carros dentro
#     c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
#     ocupados = c.fetchone()[0]
#     # reservas ativas
#     c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
#     reservados = c.fetchone()[0]
#     # vagas livres (importante incluir reservas!)
#     livres = TOTAL_LUGARES - ocupados - reservados
#     c.execute("SELECT * FROM carros WHERE ativo=1")
#     carros = c.fetchall()
#     conn.close()
#     return render_template("dashboard.html",
#                            livres=livres,
#                            ocupados=ocupados,
#                            reservados=reservados,
#                            carros=carros)
def admin_park():

    user_id = session["user_id"]

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. parques deste admin
    c.execute("""
        SELECT p.*
        FROM parques p
        JOIN admin_parques ap ON p.id = ap.parque_id
        WHERE ap.admin_id = ?
    """, (user_id,))

    parques = c.fetchall()

    conn.close()

    return render_template(
        "admin_park.html",
        parques=parques
    )

@app.route("/admin/park/<int:parque_id>")
@role_required("park_admin")
def park_detail(parque_id):

    conn = db()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. validar se admin tem acesso ao parque
    c.execute("""
        SELECT 1
        FROM admin_parques
        WHERE admin_id = ?
        AND parque_id = ?
    """, (session["user_id"], parque_id))

    if not c.fetchone():
        conn.close()
        return "Acesso negado", 403

    # 2. info parque
    c.execute("""
        SELECT *
        FROM parques
        WHERE id = ?
    """, (parque_id,))

    parque = c.fetchone()

    # 3. carros ativos
    c.execute("""
        SELECT *
        FROM carros
        WHERE parque_id = ?
        AND ativo = 1
        ORDER BY entrada DESC
    """, (parque_id,))

    carros = c.fetchall()

    # 4. reservas ativas
    c.execute("""
        SELECT *
        FROM reservas
        WHERE parque_id = ?
        AND ativo = 1
    """, (parque_id,))

    reservas = c.fetchall()

    # 5. métricas
    c.execute("""
        SELECT COUNT(*) FROM carros
        WHERE parque_id = ? AND ativo = 1
    """, (parque_id,))
    ocupados = c.fetchone()[0]

    conn.close()

    return render_template(
        "park_detail.html",
        parque=parque,
        carros=carros,
        reservas=reservas,
        ocupados=ocupados
    )
#

# Server ADmin
@app.route("/admin/parques/criar", methods=["POST"])
@role_required("server_admin")
def criar_parque():

    data = request.json
    nome = data["nome"]
    capacidade = data["capacidade"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO parques (nome, capacidade)
        VALUES (?, ?)
    """, (nome, capacidade))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/admin/parques/remover/<int:parque_id>", methods=["POST"])
@role_required("server_admin")
def remover_parque(parque_id):

    conn = db()
    c = conn.cursor()

    c.execute("""
        UPDATE parques
        SET ativo = 0
        WHERE id = ?
    """, (parque_id,))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/admin/utilizadores/criar", methods=["POST"])
@role_required("server_admin")
def criar_admin():

    data = request.json

    username = data["username"]
    password = data["password"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO utilizadores (username, password, tipo)
        VALUES (?, ?, 'park_admin')
    """, (username, password))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/admin/assign", methods=["POST"])
@role_required("server_admin")
def assign_admin():

    data = request.json
    admin_id = data["admin_id"]
    parque_id = data["parque_id"]

    conn = db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO admin_parques (admin_id, parque_id)
        VALUES (?, ?)
    """, (admin_id, parque_id))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})

@app.route("/admin/unassign", methods=["POST"])
@role_required("server_admin")
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
    """, (admin_id, parque_id))

    conn.commit()
    conn.close()

    return jsonify({"ok": True})
#

def limpar_reservas():
    conn = db()
    c = conn.cursor()

    agora = datetime.now().isoformat()

    c.execute("""
        UPDATE reservas
        SET ativo = 0
        WHERE expira < ?
        AND ativo = 1
    """, (agora,))

    conn.commit()
    conn.close()

app.run(host="0.0.0.0", port=5000)