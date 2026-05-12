import requests
import random
import time

URL = "http://127.0.0.1:5000/sensor"

NUM_LUGARES = 10

estado = [0] * NUM_LUGARES  # 0 livre, 1 ocupado

#while True:
    # simular mudança aleatória
#    i = random.randint(0, NUM_LUGARES - 1)
#    estado[i] = 1 - estado[i]
#
#    payload = {
#        "sensores": estado
#    }
#
#    try:
#        r = requests.post(URL, json=payload)
#        print(r.json())
#    except:
#        print("erro cloud")
#
#    time.sleep(3)

CLOUD_URL = "http://127.0.0.1:5000/api/estado_real"

while True:
    try:
        r = requests.get(CLOUD_URL)
        data = r.json()

        sensores = data["sensores"]

        print("Estado real:", sensores)

        # opcional: reenvia como IoT device
        requests.post(
            "http://127.0.0.1:5000/sensor",
            json={"sensores": sensores}
        )

    except Exception as e:
        print("erro:", e)

    time.sleep(2)