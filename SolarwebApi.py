import streamlit as st
import requests
import time

# Configuración de la IP del inversor
inverter_ip = "192.168.1.180"  # Cambia esto por la IP local de tu inversor

# Endpoints
powerflow_endpoint = f"http://{inverter_ip}/solar_api/v1/GetPowerFlowRealtimeData.fcgi"
meter_endpoint = f"http://{inverter_ip}/solar_api/v1/GetMeterRealtimeData.cgi"

# Título del Dashboard
st.title("Dashboard de Potencia en Tiempo Real - Fronius")

# Subtítulo
st.write("Mostrando datos en tiempo real del flujo de energía y del medidor del sistema.")

# Loop principal para actualización automática
while True:
    try:
        # Realizar la solicitud al endpoint de flujo de potencia
        powerflow_response = requests.get(powerflow_endpoint)
        powerflow_response.raise_for_status()
        powerflow_data = powerflow_response.json()["Body"]["Data"]["Site"]

        # Realizar la solicitud al endpoint del medidor
        meter_response = requests.get(meter_endpoint, params={"Scope": "System"})
        meter_response.raise_for_status()
        meter_data = meter_response.json()["Body"]["Data"]["0"]

        # Extraer información del flujo de potencia
        solar_power = powerflow_data["P_PV"] / 1000  # Convertir a kW
        grid_power = powerflow_data["P_Grid"] / 1000  # Convertir a kW
        load_power = abs(powerflow_data["P_Load"]) / 1000  # Convertir a kW y mostrar positivo

        # Extraer información del medidor
        current_phase_1 = meter_data["Current_AC_Phase_1"]
        current_phase_2 = meter_data["Current_AC_Phase_2"]
        current_phase_3 = meter_data["Current_AC_Phase_3"]
        voltage_phase_1 = meter_data["Voltage_AC_Phase_1"]
        voltage_phase_2 = meter_data["Voltage_AC_Phase_2"]
        voltage_phase_3 = meter_data["Voltage_AC_Phase_3"]
        power_real_sum = meter_data["PowerReal_P_Sum"] / 1000  # Convertir a kW
        power_reactive_sum = meter_data["PowerReactive_Q_Sum"] / 1000  # Convertir a kW
        power_apparent_sum = meter_data["PowerApparent_S_Sum"] / 1000  # Convertir a kW

        # Mostrar datos combinados en el dashboard con espacios entre bloques
        st.subheader("Potencia Actual")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Generación Solar (P_PV)", value=f"{solar_power:.2f} kW")
        with col2:
            st.metric(label="Consumo de Red (P_Grid)", value=f"{grid_power:.2f} kW")
        with col3:
            st.metric(label="Consumo Total (P_Load)", value=f"{load_power:.2f} kW")

        st.markdown("---")  # Línea divisoria para separar secciones

        st.subheader("Datos del Medidor")
        col5, col6, col7 = st.columns(3)

        with col5:
            st.metric(label="Corriente Fase 1 (A)", value=f"{current_phase_1:.2f}")
            st.metric(label="Voltaje Fase 1 (V)", value=f"{voltage_phase_1:.2f}")
        with col6:
            st.metric(label="Corriente Fase 2 (A)", value=f"{current_phase_2:.2f}")
            st.metric(label="Voltaje Fase 2 (V)", value=f"{voltage_phase_2:.2f}")
        with col7:
            st.metric(label="Corriente Fase 3 (A)", value=f"{current_phase_3:.2f}")
            st.metric(label="Voltaje Fase 3 (V)", value=f"{voltage_phase_3:.2f}")

        st.markdown("---")  # Línea divisoria para separar secciones

        st.subheader("Potencias del Sistema")
        col8, col9, col10 = st.columns(3)

        with col8:
            st.metric(label="Potencia Activa Total (kW)", value=f"{power_real_sum:.2f}")
        with col9:
            st.metric(label="Potencia Reactiva Total (kW)", value=f"{power_reactive_sum:.2f}")
        with col10:
            st.metric(label="Potencia Aparente Total (kW)", value=f"{power_apparent_sum:.2f}")

        # Pausa para la próxima actualización
        time.sleep(5)

    except requests.exceptions.RequestException as e:
        st.error(f"Error al conectarse con el inversor: {e}")
        break
    except KeyError as e:
        st.warning(f"Error al procesar los datos: {e}")
        break
