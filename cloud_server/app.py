from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "123"
CORS(app, supports_credentials=True)

# importar blueprints
from routes.auth import auth_bp
from routes.client import client_bp
from routes.parking import parking_bp
from routes.payment import payment_bp
from routes.admin_server import admin_server_bp
from routes.admin_park import admin_park_bp

app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(parking_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(admin_server_bp)
app.register_blueprint(admin_park_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)