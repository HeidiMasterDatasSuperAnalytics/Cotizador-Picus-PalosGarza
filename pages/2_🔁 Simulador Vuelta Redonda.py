import streamlit as st
import pandas as pd
import os
from datetime import datetime

RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

st.title("🔁 Simulador de Vuelta Redonda - PICUS")

def safe(x):
    return 0 if pd.isna(x) or x is None else x

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    return {}

def cargar_rutas():
    if os.path.exists(RUTA_RUTAS):
        df = pd.read_csv(RUTA_RUTAS)
        df["Ruta"] = df["Origen"] + " → " + df["Destino"]
        df["Utilidad"] = df["Ingreso Total"] - df["Costo_Total_Ruta"]
        df["% Utilidad"] = (df["Utilidad"] / df["Ingreso Total"] * 100).round(2)
        return df
    st.error("❌ No se encontró rutas_guardadas.csv")
    st.stop()

valores = cargar_datos_generales()
df_rutas = cargar_rutas()

st.subheader("📌 Paso 1: Selecciona tipo de ruta principal")
tipo_principal = st.selectbox("Tipo de ruta inicial", ["IMPO", "EXPO", "VACIO"])
rutas_principales = df_rutas[df_rutas["Tipo"] == tipo_principal].copy()

if rutas_principales.empty:
    st.warning(f"No hay rutas tipo {tipo_principal} registradas.")
    st.stop()

ruta_sel = st.selectbox("Selecciona una ruta", rutas_principales["Ruta"].unique())
rutas_filtradas = rutas_principales[rutas_principales["Ruta"] == ruta_sel].copy()
rutas_filtradas = rutas_filtradas.sort_values(by="% Utilidad", ascending=False)

cliente_idx = st.selectbox("Cliente (ordenado por % utilidad)", rutas_filtradas.index,
    format_func=lambda x: f"{rutas_filtradas.loc[x, 'Cliente']} ({rutas_filtradas.loc[x, '% Utilidad']:.2f}%)")
ruta1 = rutas_filtradas.loc[cliente_idx]

st.subheader("📌 Paso 2: Ruta intermedia sugerida (opcional)")
destino1 = ruta1["Destino"]
vacios = df_rutas[(df_rutas["Tipo"] == "VACIO") & (df_rutas["Origen"] == destino1)].copy()

opcion_intermedia = None
if not vacios.empty:
    vacios = vacios.sort_values(by="% Utilidad", ascending=False)
    idx = st.selectbox("Ruta vacía sugerida", vacios.index,
        format_func=lambda x: f"{vacios.loc[x, 'Ruta']} ({vacios.loc[x, 'Cliente']})")
    opcion_intermedia = vacios.loc[idx]

st.subheader("📌 Paso 3: Ruta final sugerida")
origen_final = opcion_intermedia["Destino"] if opcion_intermedia is not None else ruta1["Destino"]

if tipo_principal == "IMPO":
    tipo_final = "EXPO"
elif tipo_principal == "EXPO":
    tipo_final = "IMPO"
else:
    tipo_final = "EXPO"

rutas_finales = df_rutas[(df_rutas["Tipo"] == tipo_final) & (df_rutas["Origen"] == origen_final)].copy()
ruta3 = None
if not rutas_finales.empty:
    rutas_finales = rutas_finales.sort_values(by="% Utilidad", ascending=False)
    idx = st.selectbox("Ruta final sugerida", rutas_finales.index,
        format_func=lambda x: f"{rutas_finales.loc[x, 'Cliente']} - {rutas_finales.loc[x, 'Ruta']}")
    ruta3 = rutas_finales.loc[idx]

rutas_seleccionadas = [ruta1]
if opcion_intermedia is not None:
    rutas_seleccionadas.append(opcion_intermedia)
if ruta3 is not None:
    rutas_seleccionadas.append(ruta3)

st.header("🛤️ Rutas Seleccionadas")
for r in rutas_seleccionadas:
    st.markdown(f"**{r['Tipo']}** | {r['Origen']} → {r['Destino']} | Cliente: {r['Cliente']}")

modo = st.radio("Modo de viaje", ["Operador", "Team"], horizontal=True)

# =====================
# Cálculos por ruta
# =====================
detalle = []
ingreso_total = 0
costo_total = 0

for r in rutas_seleccionadas:
    ingreso = safe(r["Ingreso Total"])
    costo = safe(r["Costo_Total_Ruta"])
    tipo = r["Tipo"]
    km = safe(r["KM"])

    # Bono ISR solo si no es VACIO
    bono = float(valores.get("Bono ISR", 0)) if tipo != "VACIO" else 0
    if modo == "Team" and tipo != "VACIO":
        bono *= 2
    elif modo != "Team" and tipo == "VACIO":
        bono = 0

    # Sueldo
    if modo == "Team":
        sueldo = 650 * 2
    else:
        if tipo == "VACIO":
            sueldo = 100 if km < 100 else km * float(valores.get("Pago por km VACIO", 1.25))
        elif tipo == "IMPO":
            sueldo = km * float(valores.get("Pago por km IMPO", 1.25))
        elif tipo == "EXPO":
            sueldo = km * float(valores.get("Pago por km EXPO", 1.63))
        else:
            sueldo = 0

    # Bono de rendimiento solo si no es VACIO
    rendimiento = safe(valores.get("Bono Rendimiento", 0)) if tipo != "VACIO" else 0

    # Extras
    extras = sum(safe(r.get(campo, 0)) for campo in ["Pistas Extra", "Stop", "Falso", "Gatas", "Accesorios", "Guías"])

    total_costos = costo + sueldo + bono + extras + rendimiento
    ingreso_total += ingreso
    costo_total += total_costos

    detalle.append({
        "Tipo": tipo,
        "Cliente": r["Cliente"],
        "Ruta": r["Origen"] + " → " + r["Destino"],
        "Ingreso": ingreso,
        "Costo Base": costo,
        "Sueldo": sueldo,
        "Bono": bono,
        "Extras": extras,
        "Rendimiento": rendimiento,
        "Total Ruta": total_costos
    })

utilidad_bruta = ingreso_total - costo_total
costos_indirectos = ingreso_total * 0.35
utilidad_neta = utilidad_bruta - costos_indirectos

st.header("📊 Resultados Generales")
st.metric("Ingreso Total", f"${ingreso_total:,.2f}")
st.metric("Costo Total", f"${costo_total:,.2f}")
st.metric("Utilidad Bruta", f"${utilidad_bruta:,.2f} ({(utilidad_bruta/ingreso_total*100):.2f}%)")
st.metric("Costos Indirectos (35%)", f"${costos_indirectos:,.2f}")
st.metric("Utilidad Neta", f"${utilidad_neta:,.2f} ({(utilidad_neta/ingreso_total*100):.2f}%)")

st.subheader("📋 Detalle por Ruta")
st.dataframe(pd.DataFrame(detalle), use_container_width=True)
