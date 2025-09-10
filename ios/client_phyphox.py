import requests
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()
URL_PHYPHOX = os.getenv('URL_PHYPHOX', 'http://localhost:8080')

TO_READ = ["gyrX", "gyrY", "gyrZ"]

url_get = f"{URL_PHYPHOX}/get?{'&'.join(TO_READ)}"  

try:
    while True:
        try:
            
            response = requests.get(url_get, timeout=1)
            response.raise_for_status() 

            dados_json = response.json()

            eixo_x = dados_json['buffer'][TO_READ[0]]['buffer'][-1]
            eixo_y = dados_json['buffer'][TO_READ[1]]['buffer'][-1]
            eixo_z = dados_json['buffer'][TO_READ[2]]['buffer'][-1]

            if eixo_x is not None and eixo_y is not None and eixo_z is not None:
                print(f"Acelerômetro: X={eixo_x:.2f}, Y={eixo_y:.2f}, Z={eixo_z:.2f}", end='\r')

            time.sleep(0.1) 

        except requests.exceptions.RequestException as e:
            print(f"\nErro de conexão: {e}")
            print("Verifique se o experimento está rodando no phyphox e o acesso remoto está ativo.")
            print("Tentando reconectar em 5 segundos...")
            time.sleep(5)
        except KeyError:
            print("\nEstrutura de dados inesperada. Verifique os nomes dos sensores.")
            time.sleep(2)


except KeyboardInterrupt:
    print("\nPrograma interrompido pelo usuário.")