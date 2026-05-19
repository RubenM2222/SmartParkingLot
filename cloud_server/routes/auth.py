from flask import Blueprint, request, jsonify, session, render_template
from db import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM utilizadores WHERE username=?", (username,))
    user = c.fetchone()

    if not user:
        return jsonify({"ok": False, "msg": "Utilizador não existe"}), 404

    if user["password"] != password:
        return jsonify({"ok": False, "msg": "Password incorreta"}), 401

    session["user_id"] = user["id"]
    session["tipo"] = user["tipo"]

    return jsonify({"ok": True, "tipo": user["tipo"]})