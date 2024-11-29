import streamlit as st
import requests
import pandas as pd
import time

# Configuración de las IPs de los inversores y límites de potencia
systems = {
    "NOVACAP": {"ip": "https://api1.loca.lt", "max_power": 150},  # Límite: 150 kW
    "ALTIERI": {"ip": "https://api2.loca.lt", "max_power": 220}   # Límite: 220 kW
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

# Contenedor dinámico para actualización
main_placeholder = st.empty()

while True:
    with main_placeholder.container():
        combined_data = {}

        for system_name, system_info in systems.items():
            ip = system_info["ip"]
            max_power = system_info["max_power"]

            # Obtener datos del sistema
            data = get_system_data(system_name, ip)
            if data:
                current_time = pd.Timestamp.now()
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

                # Mostrar métricas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(f"{system_name}: Generación Solar (P_PV)", f"{data['solar_power']:.2f} kW")
                with col2:
                    st.metric(f"{system_name}: Consumo de Red (P_Grid)", f"{data['grid_power']:.2f} kW")
                with col3:
                    st.metric(f"{system_name}: Consumo Total (P_Load)", f"{data['load_power']:.2f} kW")

                # Almacenar datos combinados para gráficos
                combined_data[system_name] = data

        # Mostrar gráficos
        st.markdown("---")
        st.subheader("Gráficos Comparativos")

        for metric in ["P_PV", "P_Grid", "P_Load"]:
            chart_data = pd.DataFrame({
                "NOVACAP": historical_data["NOVACAP"][metric],
                "ALTIERI": historical_data["ALTIERI"][metric]
            })
            st.line_chart(chart_data)

        # Mostrar corrientes y voltajes
        st.markdown("---")
        st.subheader("Corrientes y Voltajes de NOVACAP y ALTIERI")

        for system_name, system_info in systems.items():
            ip = system_info["ip"]

            # Obtener datos del sistema
            data = get_system_data(system_name, ip)
            if data:
                st.subheader(f"Datos de {system_name}")
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Corrientes por Fase (A):**")
                    for i, current in enumerate(data["currents"], start=1):
                        st.metric(f"Corriente Fase {i}", f"{current:.2f} A")

                with col2:
                    st.write("**Voltajes por Fase (V):**")
                    for i, voltage in enumerate(data["voltages"], start=1):
                        st.metric(f"Voltaje Fase {i}", f"{voltage:.2f} V")

    # Pausar antes de la siguiente actualización
    time.sleep(update_interval)
