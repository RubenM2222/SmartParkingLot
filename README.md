# 📷 Flask + OCR Parking System

Sistema de gestão de parque com **Flask**, **OCR (Tesseract)** e base de dados **SQLite**.  
Permite leitura de matrículas/imagens, gestão de acessos e integração via HTTP.

---

## 🚀 Tecnologias

- Python 3
- Flask
- Flask-CORS
- Tesseract OCR
- OpenCV
- SQLite
- Raspberry Pi / Cloud VM support

---

## 📦 Instalação

### Instalar dependências principais

```bash
pip install flask flask-cors pytesseract opencv-python pillow numpy requests
```

## 🔧 Instalar Tesseract OCR

### 🪟 Windows

Download:
https://github.com/UB-Mannheim/tesseract/wiki

Instalar normalmente.

Depois configurar no `server.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 🐧 Linux / Raspberry Pi

```bash
sudo apt update
sudo apt install tesseract-ocr
```

## ▶️ Executar o projeto

```bash
python server.py
```

ou

```bash
python app.py
```

## 💳 Endpoint de pagamento

http://IP_DO_Edge_iot_pi:5001/pagamento?parque_id=1

## 🍓 Raspberry Pi (Deploy)

Instalar dependências do sistema

```bash
sudo apt update
sudo apt install python3-venv python3-full tesseract-ocr
```

Criar ambiente virtual
```bash
python3 -m venv ~/edge_iot_pi
source ~/edge_iot_pi/bin/activate
```

Instalar dependências Python
```bash
pip install --upgrade pip
pip install flask flask-cors pytesseract opencv-python numpy requests pillow
```

Executar servidor
```bash
python server.py
```

## ☁️ Cloud / VM

```bash
python app.py
```

## 📁 Estrutura do projeto

project/
├── app.py / server.py
├── database.db
├── templates/
├── static/
├── utils/
└── README.md

## 🧠 Notas importantes
- Tesseract é obrigatório para OCR funcionar
- SQLite é usado como base de dados local
- Flask serve backend do sistema
- Raspberry Pi deve usar sempre venv
- Apenas um ficheiro deve iniciar o servidor
