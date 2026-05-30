from flask import Blueprint, request, jsonify, session, render_template, redirect,url_for
from .database import db
from functools import wraps

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

@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("auth.login_page"))

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return wrapper
#def login_required(f):
#    @wraps(f)
#    def decorated_function(*args, **kwargs):
#
#        if "user_id" not in session:
#            return redirect(url_for("auth.login_page"))
#
#        response = make_response(f(*args, **kwargs))
#
#        # 🚫 impedir cache do browser
#        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
#        response.headers["Pragma"] = "no-cache"
#        response.headers["Expires"] = "0"
#
#        return response
#
#    return decorated_function