import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuración de las URLs de las APIs
systems = {
    "NOVACAP": {"ip": "https://df8b-190-15-217-99.ngrok-free.app", "max_power": 150},
    "ALTIERI": {"ip": "https://c425-190-15-217-99.ngrok-free.app", "max_power": 220}
}

# Inicialización de datos históricos
historical_data = {
    "NOVACAP": pd.DataFrame(columns=["Timestamp", "P_PV", "P_Grid", "P_Load"]),
    "ALTIERI": pd.DataFrame(columns=["Timestamp", "P_PV", "P_Grid", "P_Load"])
}

# Intervalo de actualización en segundos
update_interval = 5

# Función para obtener datos de un sistema
def get_system_data(system_name, ip):
    powerflow_endpoint = f"{ip}/solar_api/v1/GetPowerFlowRealtimeData.fcgi"
    meter_endpoint = f"{ip}/solar_api/v1/GetMeterRealtimeData.cgi"

    try:
        # Obtener datos de flujo de potencia
        powerflow_response = requests.get(powerflow_endpoint, timeout=10)
        powerflow_response.raise_for_status()
        powerflow_data = powerflow_response.json()["Body"]["Data"]["Site"]

        # Obtener datos del medidor
        meter_response = requests.get(meter_endpoint, params={"Scope": "System"}, timeout=10)
        meter_response.raise_for_status()
        meter_data = meter_response.json()["Body"]["Data"]["0"]

        # Procesar datos de potencia
        solar_power = powerflow_data["P_PV"] / 1000  # Convertir a kW
        grid_power = powerflow_data["P_Grid"] / 1000  # Convertir a kW
        load_power = abs(powerflow_data["P_Load"]) / 1000  # Convertir a kW y mostrar positivo

        # Procesar datos de corrientes y voltajes
        currents = [
            meter_data["Current_AC_Phase_1"],
            meter_data["Current_AC_Phase_2"],
            meter_data["Current_AC_Phase_3"]
        ]
        voltages = [
            meter_data["Voltage_AC_Phase_1"],
            meter_data["Voltage_AC_Phase_2"],
            meter_data["Voltage_AC_Phase_3"]
        ]

        return {
            "solar_power": solar_power,
            "grid_power": grid_power,
            "load_power": load_power,
            "currents": currents,
            "voltages": voltages
        }

    except requests.exceptions.RequestException as e:
        st.error(f"Error al conectarse con {system_name}: {e}")
        return None
    except KeyError as e:
        st.warning(f"Error al procesar los datos de {system_name}: {e}")
        return None


# Título del Dashboard
st.title("Dashboard de Potencia en Tiempo Real - Fronius")
st.write("Mostrando datos en tiempo real de los sistemas NOVACAP y ALTIERI.")

# Contenedor principal
main_placeholder = st.empty()

# Actualización de datos
for system_name, system_info in systems.items():
    ip = system_info["ip"]
    max_power = system_info["max_power"]

    # Obtener datos del sistema
    data = get_system_data(system_name, ip)
    if data:
        current_time = datetime.now()
        new_data = {
            "Timestamp": current_time,
            "P_PV": data["solar_power"],
            "P_Grid": data["grid_power"],
            "P_Load": data["load_power"]
        }
        historical_data[system_name] = pd.concat(
            [historical_data[system_name], pd.DataFrame([new_data])],
            ignore_index=True
        )

# Mostrar datos dinámicos
with main_placeholder.container():
    st.subheader("Métricas en Tiempo Real")
    for system_name, system_info in systems.items():
        data = historical_data[system_name].iloc[-1] if not historical_data[system_name].empty else None
        if data is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{system_name}: Generación Solar (P_PV)", f"{data['P_PV']:.2f} kW")
            with col2:
                st.metric(f"{system_name}: Consumo de Red (P_Grid)", f"{data['P_Grid']:.2f} kW")
            with col3:
                st.metric(f"{system_name}: Consumo Total (P_Load)", f"{data['P_Load']:.2f} kW")

# Mostrar gráficos
st.markdown("---")
st.subheader("Gráficos Comparativos")

for metric in ["P_PV", "P_Grid", "P_Load"]:
    chart_data = pd.DataFrame({
        "NOVACAP": historical_data["NOVACAP"][metric] if not historical_data["NOVACAP"].empty else [],
        "ALTIERI": historical_data["ALTIERI"][metric] if not historical_data["ALTIERI"].empty else []
    })
    st.line_chart(chart_data)

# Agregar un temporizador para recarga automática
st.markdown("---")
st.write("Actualizando en tiempo real...")
st.experimental_rerun()
