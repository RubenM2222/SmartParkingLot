from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pytesseract
import cv2
import numpy as np
import requests
import re

app = Flask(__name__)
CORS(app)

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\2222068\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/ocr', methods=['POST'])
def ocr():

    if 'image' not in request.files:
        return jsonify({'erro':'imagem não enviada'}),400

    file = request.files['image']

    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)

    config='--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    texto = pytesseract.image_to_string(thresh, config=config)

    texto = re.sub(r'[^A-Z0-9]', '', texto.upper())

    if len(texto) < 5:
        return jsonify({"erro":"matricula invalida"})

    #resposta = requests.post(
    #    "http://192.168.88.243:5000/entrada",
    #    json={"matricula": texto}
    #)
    tipo = request.args.get("tipo", "entrada")

    url = "http://127.0.0.1:5000/entrada" if tipo == "entrada" else "http://127.0.0.1:5000/saida"

    #resposta = requests.post(
    #    url,
    #    json={"matricula": texto}
    #)
    try:
        resposta = requests.post(url, json={"matricula": texto}, timeout=3)
        try:
            cloud_data = resposta.json()
        except:
            cloud_data = {"erro": "resposta invalida da cloud"}
    except:
        cloud_data = {"erro": "cloud offline"}

    #return jsonify({
    #    "matricula": texto,
    #    "servidor": resposta.json()
    #})
    return jsonify({
        "matricula": texto,
        "servidor": cloud_data
    })

app.run(host='0.0.0.0', port=5001)