from functools import wraps
from flask import session

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return "Não autenticado", 403

            if session.get("tipo") != role:
                return "Acesso negado", 403

            return f(*args, **kwargs)

        return decorated
    return wrapper