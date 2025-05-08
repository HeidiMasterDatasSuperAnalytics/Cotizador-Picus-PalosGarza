import streamlit as st
import pandas as pd
import os

st.title("📂 Administración de Archivos PICUS")

# Archivos
RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

st.subheader("📥 Descargar respaldos")

# Descargar rutas_guardadas.csv
if os.path.exists(RUTA_RUTAS):
    rutas = pd.read_csv(RUTA_RUTAS)
    st.download_button(
        label="Descargar rutas_guardadas.csv",
        data=rutas.to_csv(index=False),
        file_name="rutas_guardadas.csv",
        mime="text/csv"
    )

# Descargar datos_generales.csv
if os.path.exists(RUTA_DATOS):
    datos = pd.read_csv(RUTA_DATOS)
    st.download_button(
        label="Descargar datos_generales.csv",
        data=datos.to_csv(index=False),
        file_name="datos_generales.csv",
        mime="text/csv"
    )

st.markdown("---")
st.subheader("📤 Restaurar desde archivos")

# Subir rutas_guardadas.csv
rutas_file = st.file_uploader("Subir rutas_guardadas.csv", type="csv", key="rutas_upload")
if rutas_file:
    try:
        rutas_df = pd.read_csv(rutas_file)
        rutas_df.to_csv(RUTA_RUTAS, index=False)
        st.success("✅ Rutas restauradas correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al cargar rutas: {e}")

# Subir datos_generales.csv
datos_file = st.file_uploader("Subir datos_generales.csv", type="csv", key="datos_upload")
if datos_file:
    try:
        datos_df = pd.read_csv(datos_file)
        datos_df.to_csv(RUTA_DATOS, index=False)
        st.success("✅ Datos generales restaurados correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al cargar datos generales: {e}")
