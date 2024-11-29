import requests

# Configuración
inverter_ip = "192.168.1.181"  # Cambia por la IP local de tu inversor
endpoints = [
    "/solar_api/v1/GetPowerFlowRealtimeData.fcgi",
    "/solar_api/v1/GetInverterRealtimeData.cgi",
    "/solar_api/v1/GetMeterRealtimeData.cgi",
    "/solar_api/v1/GetStorageRealtimeData.cgi",
    "/solar_api/v1/GetDeviceList.cgi",
    "/solar_api/v1/GetSystemStatus.cgi"
]

# Probar cada endpoint
for endpoint in endpoints:
    url = f"http://{inverter_ip}{endpoint}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Endpoint disponible: {endpoint}")
            print(response.json())  # Mostrar datos devueltos
        else:
            print(f"❌ Endpoint no disponible: {endpoint} (Código {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al probar el endpoint {endpoint}: {e}")
