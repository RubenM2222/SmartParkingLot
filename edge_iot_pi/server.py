from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pytesseract
import cv2
import numpy as np
import requests, socket, re, os
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

#pytesseract.pytesseract.tesseract_cmd = r'C:\Users\2222068\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\ruben\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'erro':'imagem não enviada'}), 400

    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    # 1. REDIMENSIONAR (Crucial para fotos de telemóvel)
    # Se a imagem for gigante, o Tesseract "afoga-se". Vamos normalizar.
    max_dimension = 1200
    height, width = img.shape[:2]
    if width > max_dimension or height > max_dimension:
        scaling_factor = max_dimension / float(max(width, height))
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)

    # 2. CONVERTER PARA CINZA
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. TRATAMENTO DE LUZ (Denoising e Contraste)
    # Remove o "grão" da foto sem borrar as letras
    gray = cv2.bilateralFilter(gray, 11, 17, 17) 

    # 4. THRESHOLD ADAPTATIVO (O segredo do sucesso)
    # Em vez de usar 150, ele analisa a luz de cada pedaço da foto individualmente.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)

    # 6. OCR
    config = '--oem 3 --psm 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    texto = pytesseract.image_to_string(thresh, config=config)

    # Limpeza de caracteres
    texto = re.sub(r'[^A-Z0-9]', '', texto.upper())

    if len(texto) < 5:
        # Enviamos as chaves que o JS espera, mas com aviso de erro
        return jsonify({
            "matricula": texto if texto else "Não lida", 
            "servidor": {"erro": "Matrícula inválida ou muito curta"},
            "erro": "Falha no OCR"
        })

    #resposta = requests.post(
    #    "http://192.168.88.243:5000/entrada",
    #    json={"matricula": texto}
    #)
    tipo = request.args.get("tipo", "entrada")

    #url = "http://127.0.0.1:5000/entrada" if tipo == "entrada" else "http://127.0.0.1:5000/saida"

    parque_id = get_parque_id()
    if not parque_id:
        parque_id = request.args.get("parque_id", type=int)

    if not parque_id:
        return jsonify({
        "erro": "Parque não identificado (hostname inválido e sem fallback)"
        }), 400
    #resposta = requests.post(
    #    url,
    #    json={"matricula": texto}
    #)
    # DYNAMIC IP FETCHING HERE
    base_url = get_cloud_base_url()
    url = f"{base_url}/{tipo}/{parque_id}"
    
    #url = f"http://127.0.0.1:5000/{tipo}/{parque_id}"
    
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

def get_parque_id():
    hostname = socket.gethostname()

    match = re.search(r'parking(\d+)', hostname)
    if match:
        return int(match.group(1))

    return None

# --- helper function to get target api url ---
def get_cloud_base_url():
    """Reads the target server IP/URL from a local txt file."""
    filename = "ip.txt"
    default_url = "http://127.0.0.1:5000"
    
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found. Using default: {default_url}")
        return default_url
        
    try:
        with open(filename, "r") as file:
            ip = file.read().strip()
            if not ip:
                return default_url
            
            # If they didn't type http:// or https://, add it temporarily so urlparse can read it
            if not ip.startswith(("http://", "https://")):
                parsed = urlparse(f"http://{ip}")
            else:
                parsed = urlparse(ip)
            
            # Extract the port. If no port was specified, parsed.port will be None
            scheme = parsed.scheme if parsed.scheme else "http"
            hostname = parsed.hostname if parsed.hostname else "127.0.0.1"
            port = parsed.port if parsed.port else 5000
            
            return f"{scheme}://{hostname}:{port}"
    except Exception as e:
        print(f"Error reading {filename}: {e}. Using default.")
        return default_url

def get_parque_id():
    hostname = socket.gethostname()
    match = re.search(r'parking(\d+)', hostname)
    if match:
        return int(match.group(1))
    return None

@app.route("/pagamento")
def pagamento():
    return render_template("pagamento.html")

app.run(host='0.0.0.0', port=5001)