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
pip3 install flask flask-cors pytesseract opencv-python pillow  

python3 server.py  