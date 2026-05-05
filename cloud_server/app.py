from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)

TOTAL_LUGARES = 10

def db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS carros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT,
        entrada TEXT,
        saida TEXT,
        preco REAL,
        tempo INTEGER,
        ativo INTEGER
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula TEXT,
        inicio TEXT,
        expira TEXT,
        ativo INTEGER
    )
    ''')

    conn.commit()
    conn.close()

init()

@app.route("/")
def cliente():
    conn = db()
    c = conn.cursor()

    # ocupados
    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    # reservas
    c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
    reservados = c.fetchone()[0]

    livres = TOTAL_LUGARES - ocupados - reservados

    conn.close()

    return render_template("cliente.html",
                           livres=livres,
                           ocupados=ocupados)

@app.route("/admin")
def dashboard():
    
    password = request.args.get("key")

    if password != "admin123":
        return "Acesso negado"
    # http://IP:5000/admin?key=admin123


    conn = db()
    c = conn.cursor()

    # carros dentro
    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    # reservas ativas
    c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
    reservados = c.fetchone()[0]

    # vagas livres (importante incluir reservas!)
    livres = TOTAL_LUGARES - ocupados - reservados

    c.execute("SELECT * FROM carros WHERE ativo=1")
    carros = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           livres=livres,
                           ocupados=ocupados,
                           reservados=reservados,
                           carros=carros)

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

@app.route("/entrada", methods=["POST"])
def entrada():
    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # VERIFICAR SE JÁ ESTÁ DENTRO
    c.execute("""
        SELECT * FROM carros 
        WHERE matricula = ? AND ativo = 1
    """, (matricula,))

    existe = c.fetchone()

    if existe:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Veículo já está dentro do parque"
        })

    # verificar reserva ativa
    c.execute("""
        SELECT * FROM reservas
        WHERE matricula=? AND ativo=1
    """, (matricula,))

    reserva = c.fetchone()

    if reserva:
        # consumir reserva
        c.execute("""
            UPDATE reservas
            SET ativo=0
            WHERE matricula=? AND ativo=1
        """, (matricula,))

    # VERIFICAR CAPACIDADE
    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    if ocupados >= TOTAL_LUGARES:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Parque cheio"
        })

    # 3. REGISTAR ENTRADA
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO carros (matricula, entrada, ativo)
        VALUES (?, ?, 1)
    """, (matricula, agora))

    conn.commit()
    conn.close()

    limpar_reservas()
    return jsonify({
        "ok": True,
        "msg": "Entrada autorizada"
    })

@app.route("/saida", methods=["POST"])
def saida():
    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # verificar se está ativo
    c.execute("""
        SELECT * FROM carros
        WHERE matricula=? AND ativo=1
    """, (matricula,))

    carro = c.fetchone()

    if not carro:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Veículo não está no parque"
        })

    agora = datetime.now()

    entrada_dt = datetime.strptime(carro["entrada"], "%Y-%m-%d %H:%M:%S")

    # calcular tempo (minutos)
    tempo_min = int((agora - entrada_dt).total_seconds() / 60)

    # regra simples de preço
    preco = max(1, tempo_min * 0.05)  # mínimo 1€

    agora_str = agora.strftime("%Y-%m-%d %H:%M:%S")

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
        "tempo_min": tempo_min,
        "preco": round(preco, 2)
    })

@app.route("/reservar", methods=["POST"])
def reservar():
    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    # ver se já tem reserva ativa
    c.execute("""
        SELECT * FROM reservas
        WHERE matricula=? AND ativo=1
    """, (matricula,))
    
    if c.fetchone():
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Já tens uma reserva ativa"
        })

    # contar ocupados + reservas
    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM reservas WHERE ativo=1")
    reservados = c.fetchone()[0]

    if ocupados + reservados >= TOTAL_LUGARES:
        conn.close()
        return jsonify({
            "ok": False,
            "msg": "Sem vagas disponíveis"
        })

    agora = datetime.now()
    expira = agora + timedelta(minutes=2)  # timeout curto para testes

    c.execute("""
        INSERT INTO reservas (matricula, inicio, expira, ativo)
        VALUES (?, ?, ?, 1)
    """, (
        matricula,
        agora.strftime("%Y-%m-%d %H:%M:%S"),
        expira.strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    conn.commit()
    conn.close()

    limpar_reservas()
    return jsonify({
        "ok": True,
        "msg": "Reserva criada (2 min)"
    })

def limpar_reservas():
    conn = db()
    c = conn.cursor()

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        UPDATE reservas
        SET ativo=0
        WHERE expira < ? AND ativo=1
    """, (agora,))

    conn.commit()
    conn.close()

app.run(host="0.0.0.0", port=5000)