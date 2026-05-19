from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

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
        ativo INTEGER
    )
    ''')

    conn.commit()
    conn.close()

init()

@app.route("/")
def dashboard():
    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    livres = TOTAL_LUGARES - ocupados

    c.execute("SELECT * FROM carros WHERE ativo=1")
    carros = c.fetchall()

    conn.close()

    return render_template("dashboard.html",
                           livres=livres,
                           ocupados=ocupados,
                           carros=carros)

@app.route("/entrada", methods=["POST"])
def entrada():
    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM carros WHERE ativo=1")
    ocupados = c.fetchone()[0]

    if ocupados >= TOTAL_LUGARES:
        return jsonify({"ok": False, "msg": "Parque cheio"})

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("INSERT INTO carros (matricula, entrada, ativo) VALUES (?, ?, 1)",
              (matricula, agora))

    conn.commit()
    conn.close()

    return jsonify({"ok": True, "msg": "Entrada autorizada"})

@app.route("/saida", methods=["POST"])
def saida():
    data = request.json
    matricula = data["matricula"]

    conn = db()
    c = conn.cursor()

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
    UPDATE carros
    SET saida=?, ativo=0
    WHERE matricula=? AND ativo=1
    """, (agora, matricula))

    conn.commit()
    conn.close()

    return jsonify({"ok": True, "msg": "Saida registada"})

app.run(host="0.0.0.0", port=5000)