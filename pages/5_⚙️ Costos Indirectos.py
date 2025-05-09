import streamlit as st
import pandas as pd
import os

RUTA_DATOS = "datos_generales.csv"

st.title("⚙️ Configuración de Costos Indirectos")

# Valores por defecto si no existen en el CSV
valores_indirectos = {
    "Costo Indirecto RL": 7281.31,
    "Costo Indirecto RC": 7350.44
}

# Funciones para cargar y guardar

def cargar_datos_indirectos():
    if os.path.exists(RUTA_DATOS):
        df = pd.read_csv(RUTA_DATOS)
        valores = df.set_index("Parametro").to_dict()["Valor"]
        for clave in valores_indirectos:
            if clave not in valores:
                valores[clave] = valores_indirectos[clave]
        return valores
    else:
        return valores_indirectos.copy()

def guardar_datos_indirectos(valores):
    if os.path.exists(RUTA_DATOS):
        df_actual = pd.read_csv(RUTA_DATOS)
    else:
        df_actual = pd.DataFrame(columns=["Parametro", "Valor"])

    dict_actual = df_actual.set_index("Parametro").to_dict().get("Valor", {})
    dict_actual.update(valores)
    df_final = pd.DataFrame(dict_actual.items(), columns=["Parametro", "Valor"])
    df_final.to_csv(RUTA_DATOS, index=False)

# Mostrar formulario
valores = cargar_datos_indirectos()

st.subheader("💼 Costos indirectos por tipo de ruta")

for clave in valores_indirectos:
    valores[clave] = st.number_input(clave, value=float(valores.get(clave, valores_indirectos[clave])), step=1.0)

if st.button("Guardar Costos Indirectos"):
    guardar_datos_indirectos(valores)
    st.success("✅ Costos indirectos guardados correctamente.")
