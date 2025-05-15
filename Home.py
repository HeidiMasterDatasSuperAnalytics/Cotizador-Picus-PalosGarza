import streamlit as st
from PIL import Image
import base64
from io import BytesIO

# Ruta al logo (debe estar en el mismo directorio o usar ruta relativa desde /page)
LOGO_PATH = "Picus BG.png"

# Convertir logo a base64 para manejo de modo oscuro/claro
@st.cache_data
def image_to_base64(img_path):
    with open(img_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

logo_b64 = image_to_base64(LOGO_PATH)

# Mostrar encabezado con logo
st.markdown(f"""
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{logo_b64}" style="height: 120px; margin-bottom: 20px;">
    </div>
    <h1 style='text-align: center; color: #003366;'>Sistema Cotizador PICUS</h1>
    <p style='text-align: center;'>Control de rutas, costos, programación y simulación de utilidad</p>
    <hr style='margin-top: 20px; margin-bottom: 30px;'>
""", unsafe_allow_html=True)

# Instrucciones o navegación
st.subheader("📂 Módulos disponibles")
st.markdown("""
- **🛣️ Captura de Rutas:** Ingreso de datos de nuevas rutas
- **🔍 Consulta Individual de Ruta:** Análisis detallado por registro
- **🔁 Simulador Vuelta Redonda:** Combinaciones IMPO + VACIO + EXPO
- **🚚 Programación de Viajes:** Registro y simulación de tráficos ida y vuelta
- **🗂️ Gestión de Rutas:** Editar y eliminar rutas existentes
- **📂 Archivos:** Descargar / cargar respaldos de datos
""")

st.info("Selecciona una opción desde el menú lateral para comenzar")
