from flask import Flask
from flask_cors import CORS
import threading

from routes.auth import auth_bp
from routes.parking import parking_bp
from routes.payment import payment_bp
from routes.admin_park import admin_park_bp
from routes.admin_server import admin_server_bp
from routes.client import client_bp
#from routes.sensors import sensor_bp
from routes.database import init
from scheduler import limpeza_automatica

app = Flask(__name__)

CORS(app, supports_credentials=True)

app.secret_key = "123"

@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.register_blueprint(auth_bp)
app.register_blueprint(parking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(admin_park_bp)
app.register_blueprint(admin_server_bp)
app.register_blueprint(client_bp)
#app.register_blueprint(sensor_bp)

init()

if __name__ == "__main__":
    
    threading.Thread(
        target=limpeza_automatica,
        daemon=True
    ).start()
    app.run(host="0.0.0.0", port=5000)