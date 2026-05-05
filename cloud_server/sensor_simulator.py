import requests
import random
import time

URL = "http://127.0.0.1:5000/sensor"

NUM_LUGARES = 10

estado = [0] * NUM_LUGARES  # 0 livre, 1 ocupado

while True:
    # simular mudança aleatória
    i = random.randint(0, NUM_LUGARES - 1)
    estado[i] = 1 - estado[i]

    payload = {
        "sensores": estado
    }

    try:
        r = requests.post(URL, json=payload)
        print(r.json())
    except:
        print("erro cloud")

    time.sleep(3)