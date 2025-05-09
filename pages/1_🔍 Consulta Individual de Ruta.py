import streamlit as st
import pandas as pd
import os

RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

def safe_number(x):
    return 0 if pd.isna(x) else x

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    else:
        return {}

valores = cargar_datos_generales()

st.title("\U0001F50D Consulta Individual de Ruta")

if os.path.exists(RUTA_RUTAS):
    df = pd.read_csv(RUTA_RUTAS)

    st.subheader("\ud83d\udccc Selecciona una Ruta")
    index_sel = st.selectbox(
        "Selecciona \u00edndice",
        df.index.tolist(),
        format_func=lambda x: f"{df.loc[x, 'Tipo']} - {df.loc[x, 'Cliente']} - {df.loc[x, 'Origen']} → {df.loc[x, 'Destino']}"
    )

    ruta = df.loc[index_sel]
    clasificacion = ruta.get("Clasificación Ruta", "RL")
    if clasificacion == "RC":
        costo_indirecto_fijo = float(valores.get("Costo Indirecto RC", 7350.44))
    else:
        costo_indirecto_fijo = float(valores.get("Costo Indirecto RL", 7281.31))

    ingreso_total = safe_number(ruta["Ingreso Total"])
    costo_total = safe_number(ruta["Costo_Total_Ruta"])
    utilidad_bruta = ingreso_total - costo_total
    utilidad_neta = utilidad_bruta - costo_indirecto_fijo

    porcentaje_bruta = (utilidad_bruta / ingreso_total * 100) if ingreso_total > 0 else 0
    porcentaje_neta = (utilidad_neta / ingreso_total * 100) if ingreso_total > 0 else 0

    def colored_bold(label, value, condition):
        color = "green" if condition else "red"
        return f"<strong>{label}:</strong> <span style='color:{color}; font-weight:bold'>{value}</span>"

    # =====================
    # 📊 Ingresos y Utilidades
    # =====================
    st.markdown("---")
    st.subheader("\ud83d\udcca Ingresos y Utilidades")

    st.write(f"**Ingreso Total:** ${ingreso_total:,.2f}")
    st.write(f"**Costo Total:** ${costo_total:,.2f}")
    st.markdown(colored_bold("Utilidad Bruta", f"${utilidad_bruta:,.2f}", utilidad_bruta >= 0), unsafe_allow_html=True)
    st.markdown(colored_bold("% Utilidad Bruta", f"{porcentaje_bruta:.2f}%", porcentaje_bruta >= 50), unsafe_allow_html=True)
    st.write(f"**Costos Indirectos ({clasificacion}):** ${costo_indirecto_fijo:,.2f}")
    st.markdown(colored_bold("Utilidad Neta", f"${utilidad_neta:,.2f}", utilidad_neta >= 0), unsafe_allow_html=True)
    st.markdown(colored_bold("% Utilidad Neta", f"{porcentaje_neta:.2f}%", porcentaje_neta >= 15), unsafe_allow_html=True)

    # =====================
    # 📋 Detalles y Costos
    # =====================
    st.markdown("---")
    st.subheader("\ud83d\udccb Detalles y Costos de la Ruta")

    detalles = [
        f"Fecha: {ruta['Fecha']}",
        f"Tipo: {ruta['Tipo']}",
        f"Clasificación: {clasificacion}",
        f"Modo de viaje: {ruta.get('Modo_Viaje', 'Operador')}",
        f"Cliente: {ruta['Cliente']}",
        f"Origen → Destino: {ruta['Origen']} → {ruta['Destino']}",
        f"KM: {safe_number(ruta['KM']):,.2f}",
        f"Moneda Flete: {ruta['Moneda']}",
        f"Ingreso Flete Original: ${safe_number(ruta['Ingreso_Original']):,.2f}",
        f"Tipo de cambio: {safe_number(ruta['Tipo de cambio']):,.2f}",
        f"Ingreso Flete Convertido: ${safe_number(ruta['Ingreso Flete']):,.2f}",
        f"Moneda Cruce: {ruta['Moneda_Cruce']}",
        f"Ingreso Cruce Original: ${safe_number(ruta['Cruce_Original']):,.2f}",
        f"Tipo cambio Cruce: {safe_number(ruta['Tipo cambio Cruce']):,.2f}",
        f"Ingreso Cruce Convertido: ${safe_number(ruta['Ingreso Cruce']):,.2f}",
        f"Moneda Costo Cruce: {ruta['Moneda Costo Cruce']}",
        f"Costo Cruce Original: ${safe_number(ruta['Costo Cruce']):,.2f}",
        f"Costo Cruce Convertido: ${safe_number(ruta['Costo Cruce Convertido']):,.2f}",
        f"Diesel Camion: ${safe_number(ruta['Costo_Diesel_Camion']):,.2f}",
        f"Sueldo Operador: ${safe_number(ruta['Sueldo_Operador']):,.2f}",
        f"Bono: ${safe_number(ruta['Bono']):,.2f}",
        f"Casetas: ${safe_number(ruta['Casetas']):,.2f}",
        "**Extras:**",
        f"- Movimiento Local: ${safe_number(ruta['Movimiento_Local']):,.2f}",
        f"- Puntualidad: ${safe_number(ruta['Puntualidad']):,.2f}",
        f"- Pensión: ${safe_number(ruta['Pension']):,.2f}",
        f"- Estancia: ${safe_number(ruta['Estancia']):,.2f}"
    ]

    for line in detalles:
        st.write(line)
else:
    st.warning("⚠️ No hay rutas guardadas todavía.")
