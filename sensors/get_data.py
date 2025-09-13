import requests
import time
import os
from dotenv import load_dotenv
import pyvista as pv
import numpy as np
import pandas as pd

load_dotenv()
URL_PHYPHOX = os.getenv('URL_PHYPHOX', 'http://localhost:8080')

TO_READ = [
    "gyroX", "gyroY", "gyroZ", "gyro_time", # gyroscope data
    "accX", "accY", "accZ", "acc_time", # accelerometer data
    "graX", "graY", "graZ", "graT",  # gravity data
    "lin_accX", "lin_accY", "lin_accZ", "lin_acc_time"  # linear acceleration data
]

url_get = f"{URL_PHYPHOX}/get?{'&'.join(TO_READ)}"  

measures = dict()
measures_count = 0

while True:

    response = requests.get(url_get, timeout=1)

    response.raise_for_status() 

    data = response.json()

    grax = data['buffer']['graX']['buffer'][0]
    gray = data['buffer']['graY']['buffer'][0]
    graz = data['buffer']['graZ']['buffer'][0]
    grat = data['buffer']['graT']['buffer'][0]

    print(f"Gravity: x={grax:.2f}, y={gray:.2f}, z={graz:.2f}, t={grat:.2f}")

    lin_accx = data['buffer']['lin_accX']['buffer'][0]
    lin_accy = data['buffer']['lin_accY']['buffer'][0]
    lin_accz = data['buffer']['lin_accZ']['buffer'][0]
    lin_acct = data['buffer']['lin_acc_time']['buffer'][0]

    print(f"Linear Acceleration: x={lin_accx:.2f}, y={lin_accy:.2f}, z={lin_accz:.2f}, t={lin_acct:.2f}")

    accx = data['buffer']['accX']['buffer'][0]
    accy = data['buffer']['accY']['buffer'][0]
    accz = data['buffer']['accZ']['buffer'][0]
    acct = data['buffer']['acc_time']['buffer'][0]

    print(f"Acceleration: x={accx:.2f}, y={accy:.2f}, z={accz:.2f}, t={acct:.2f}")

    gyrx = data['buffer']['gyroX']['buffer'][0]
    gyry = data['buffer']['gyroY']['buffer'][0]
    gyrz = data['buffer']['gyroZ']['buffer'][0]
    gyrt = data['buffer']['gyro_time']['buffer'][0]

    print(f"Gyroscope: x={gyrx:.2f}, y={gyry:.2f}, z={gyrz:.2f}, t={gyrt:.2f}")

    print("-" * 40)
    time.sleep(0.1)

    measures[measures_count] = {
        'gravity': (np.array([grax, gray, graz]), grat),
        'linear_acceleration': (np.array([lin_accx, lin_accy, lin_accz]), lin_acct),
        'acceleration': (np.array([accx, accy, accz]), acct),
        'gyroscope': (np.array([gyrx, gyry, gyrz]), gyrt)
    }
    
    measures_count += 1
    print(measures_count)
    if measures_count >= 1000:
        break


print("=+"*40)
print(measures)
pd.DataFrame(measures)