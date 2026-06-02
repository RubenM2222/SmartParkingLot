# Projeto Flask + OCR (Python)

Estou a utilizar Flask para o Python e comunicação via HTTP.  
A base de dados está em SQLite.

---

## 📦 Instalação de dependências

pip3 install flask pytesseract opencv-python pillow  
pip3 install flask-cors  

---

## ▶️ Executar o servidor

python server.py
python app.py  

---

## 🌐 Frontend (HTML)

O Flask já serve o HTML, por isso não é necessário usar:

python -m http.server 8000 

Usar /admin?key=admin123 para aceder ao dashboard admin(ja nao é necessario)

---

## 🔧 Instalar Tesseract OCR (Windows)

Download:  
https://github.com/UB-Mannheim/tesseract/wiki  

Instalar normalmente no Windows.

---

## 📍 Caminho do Tesseract

Exemplo:

C:\Program Files\Tesseract-OCR\tesseract.exe  

---

## ⚙️ Configurar no server.py

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  

---

## ☁️ Servidor em Cloud (VM)

python app.py  

---

## 🍓 Raspberry Pi

sudo apt install tesseract-ocr 

(nao me lembro se preciso do pillow)pip3 install flask flask-cors pytesseract opencv-python pillow 

pip install Flask flask-cors pytesseract opencv-python numpy requests

python3 server.py 

### No rapsberry
Install venv support if needed
sudo apt update
sudo apt install python3-venv python3-full

Create a virtual environment
python3 -m venv ~/edge_iot_pi

Activate it
source ~/edge_iot_pi/bin/activate

Upgrade pip
pip install --upgrade pip

Install your packages
pip install Flask flask-cors pytesseract opencv-python numpy requests

sudo apt install tesseract-ocr 

**after**
cd ~/edge_iot_pi
source venv/bin/activate
python app.py


# Importante

para aceder ao pagamento tem de ser 
http://ip:5001/pagamento&parque_id=1