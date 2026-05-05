from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\2222068\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'erro': 'imagem não enviada'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'erro': 'ficheiro vazio'}), 400

    try:
        npimg = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'erro': 'imagem inválida'}), 400

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        config = '-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 6'
        texto = pytesseract.image_to_string(thresh, config=config)

        return jsonify({'texto': texto})

    except Exception as e:
        return jsonify({'erro': str(e)}), 500

app.run(host='0.0.0.0', port=5000)