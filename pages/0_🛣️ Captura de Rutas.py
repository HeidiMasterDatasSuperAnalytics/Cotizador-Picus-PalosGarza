import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Rutas de archivos
RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

if "revisar_ruta" not in st.session_state:
    st.session_state.revisar_ruta = False

# Datos generales (solo los básicos)
valores_por_defecto = {
    "Rendimiento Camion": 2.5,
    "Costo Diesel": 24.0,
    "Pago x KM (General)": 1.50,
    "Bono ISR IMSS": 462.66,
    "Tipo de cambio USD": 17.5,
    "Tipo de cambio MXN": 1.0
}

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    else:
        return valores_por_defecto.copy()

def guardar_datos_generales(valores):
    df = pd.DataFrame(valores.items(), columns=["Parametro", "Valor"])
    df.to_csv(RUTA_DATOS, index=False)

def safe_number(x):
    return 0 if (x is None or (isinstance(x, float) and pd.isna(x))) else x

valores = cargar_datos_generales()

st.title("🚛 Captura de Rutas PICUS")

# Configurar Datos Generales
with st.expander("⚙️ Configurar Datos Generales"):
    for key in valores_por_defecto:
        valores[key] = st.number_input(key, value=float(valores.get(key, valores_por_defecto[key])), step=0.1)
    if st.button("Guardar Datos Generales"):
        guardar_datos_generales(valores)
        st.success("✅ Datos Generales guardados correctamente.")

st.markdown("---")

if os.path.exists(RUTA_RUTAS):
    df_rutas = pd.read_csv(RUTA_RUTAS)
else:
    df_rutas = pd.DataFrame()

st.subheader("🚣️ Nueva Ruta")

with st.form("captura_ruta"):
    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Fecha", value=datetime.today())
        tipo = st.selectbox("Tipo de Ruta", ["IMPO", "EXPO", "VACIO"])
        clasificacion_ruta = st.selectbox("Clasificación Ruta", ["RL", "RC"])
        cliente = st.text_input("Nombre Cliente")
        origen = st.text_input("Origen")
        destino = st.text_input("Destino")
        modo_viaje = st.selectbox("Modo de viaje", ["Operador", "Team"])
        casetas = st.number_input("Casetas", min_value=0.0)

    with col2:
        km = st.number_input("Kilómetros", min_value=0.0)
        moneda_ingreso = st.selectbox("Moneda Ingreso Flete", ["MXN", "USD"])
        ingreso_flete = st.number_input("Ingreso Flete", min_value=0.0)
        moneda_cruce = st.selectbox("Moneda Ingreso Cruce", ["MXN", "USD"])
        ingreso_cruce = st.number_input("Ingreso Cruce", min_value=0.0)
        moneda_costo_cruce = st.selectbox("Moneda Costo Cruce", ["MXN", "USD"])
        costo_cruce = st.number_input("Costo Cruce", min_value=0.0)
        movimiento_local = st.number_input("Movimiento Local", min_value=0.0)
        puntualidad = st.number_input("Puntualidad", min_value=0.0)
        pension = st.number_input("Pensión", min_value=0.0)
        estancia = st.number_input("Estancia", min_value=0.0)

    revisar = st.form_submit_button("🔍 Revisar Ruta")
    if revisar:
        st.session_state.revisar_ruta = True
        st.session_state.datos_captura = {
            "fecha": fecha, "tipo": tipo, "clasificacion_ruta": clasificacion_ruta,
            "cliente": cliente, "origen": origen, "destino": destino, "modo_viaje": modo_viaje,
            "km": km, "moneda_ingreso": moneda_ingreso, "ingreso_flete": ingreso_flete,
            "moneda_cruce": moneda_cruce, "ingreso_cruce": ingreso_cruce,
            "moneda_costo_cruce": moneda_costo_cruce, "costo_cruce": costo_cruce,
            "movimiento_local": movimiento_local, "puntualidad": puntualidad,
            "pension": pension, "estancia": estancia, "casetas": casetas
        }

if st.session_state.revisar_ruta and st.button("📅 Guardar Ruta"):
    d = st.session_state.datos_captura

    tipo_cambio_flete = valores["Tipo de cambio USD"] if d["moneda_ingreso"] == "USD" else valores["Tipo de cambio MXN"]
    tipo_cambio_cruce = valores["Tipo de cambio USD"] if d["moneda_cruce"] == "USD" else valores["Tipo de cambio MXN"]
    tipo_cambio_costo_cruce = valores["Tipo de cambio USD"] if d["moneda_costo_cruce"] == "USD" else valores["Tipo de cambio MXN"]

    ingreso_flete_convertido = d["ingreso_flete"] * tipo_cambio_flete
    ingreso_cruce_convertido = d["ingreso_cruce"] * tipo_cambio_cruce
    costo_cruce_convertido = d["costo_cruce"] * tipo_cambio_costo_cruce
    ingreso_total = ingreso_flete_convertido + ingreso_cruce_convertido

    costo_diesel_camion = (d["km"] / valores["Rendimiento Camion"]) * valores["Costo Diesel"]

    pago_km = valores["Pago x KM (General)"]

    if d["tipo"] in ["IMPO", "EXPO"]:
        sueldo = d["km"] * pago_km
        bono = valores["Bono ISR IMSS"]
    elif d["tipo"] == "VACIO":
        if d["km"] < 1000:
            sueldo = 200
        else:
            sueldo = d["km"] * pago_km
        bono = 0

    if d["modo_viaje"] == "Team":
        sueldo *= 2

    extras = sum([
        safe_number(d["movimiento_local"]),
        safe_number(d["puntualidad"]),
        safe_number(d["pension"]),
        safe_number(d["estancia"])
    ])

    costo_total = costo_diesel_camion + sueldo + bono + d["casetas"] + extras + costo_cruce_convertido

    nueva_ruta = {
        "Fecha": d["fecha"], "Tipo": d["tipo"], "Clasificación Ruta": d["clasificacion_ruta"],
        "Cliente": d["cliente"], "Origen": d["origen"], "Destino": d["destino"],
        "Modo_Viaje": d["modo_viaje"], "KM": d["km"],
        "Moneda": d["moneda_ingreso"], "Ingreso_Original": d["ingreso_flete"], "Tipo de cambio": tipo_cambio_flete,
        "Ingreso Flete": ingreso_flete_convertido, "Moneda_Cruce": d["moneda_cruce"], "Cruce_Original": d["ingreso_cruce"],
        "Tipo cambio Cruce": tipo_cambio_cruce, "Ingreso Cruce": ingreso_cruce_convertido,
        "Moneda Costo Cruce": d["moneda_costo_cruce"], "Costo Cruce": d["costo_cruce"],
        "Costo Cruce Convertido": costo_cruce_convertido,
        "Ingreso Total": ingreso_total, "Pago por KM": pago_km,
        "Sueldo_Operador": sueldo, "Bono": bono,
        "Casetas": d["casetas"], "Movimiento_Local": d["movimiento_local"],
        "Puntualidad": d["puntualidad"], "Pension": d["pension"], "Estancia": d["estancia"],
        "Costo_Diesel_Camion": costo_diesel_camion, "Costo_Extras": extras, "Costo_Total_Ruta": costo_total
    }

    df_rutas = pd.concat([df_rutas, pd.DataFrame([nueva_ruta])], ignore_index=True)
    df_rutas.to_csv(RUTA_RUTAS, index=False)
    st.success("✅ Ruta guardada exitosamente.")
    st.session_state.revisar_ruta = False
    del st.session_state["datos_captura"]
    st.experimental_rerun()
