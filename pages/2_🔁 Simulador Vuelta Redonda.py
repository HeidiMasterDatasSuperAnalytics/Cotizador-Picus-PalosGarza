
# Simulador de Vuelta Redonda (Formato Igloo, Cálculos PICUS)
# ------------------------------------------------------------
# - Diseño por pasos visual como Igloo
# - Tabla resumen de rutas seleccionadas
# - Sueldo y bono ISR correctos por modo de viaje
# - Bono rendimiento incluido
# - Costos extras aplicados
# - Costos indirectos como 35% del ingreso total

import streamlit as st
import pandas as pd
import os

RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

def safe(x): return 0 if pd.isna(x) or x is None else x

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    return {
        "Rendimiento Camion": 2.5,
        "Costo Diesel": 24.0,
        "Pago x KM (General)": 1.50,
        "Bono ISR IMSS": 462.66,
        "Bono Rendimiento": 250.0,
    }

def calcular_costos(tramo, valores):
    km = safe(tramo.get("KM", 0))
    modo = tramo.get("Modo_Viaje", "Operador")
    tipo = tramo.get("Tipo", "IMPO")
    casetas = safe(tramo.get("Casetas", 0))
    bono_rend = float(valores["Bono Rendimiento"])
    pago_km = float(valores["Pago x KM (General)"])
    bono_isr = float(valores["Bono ISR IMSS"])
    diesel = (km / float(valores["Rendimiento Camion"])) * float(valores["Costo Diesel"])

    extras = sum([safe(tramo.get(x, 0)) for x in [
        "Movimiento_Local", "Puntualidad", "Pension", "Estancia", "Pistas Extra", 
        "Stop", "Falso", "Gatas", "Accesorios", "Guías"
    ]])

    if modo == "Team":
        sueldo = 1300
        bono = bono_isr * 2
    else:
        sueldo = 100 if tipo == "VACIO" and km < 100 else km * pago_km
        bono = 0 if tipo == "VACIO" else bono_isr

    costo_cruce = safe(tramo.get("Costo Cruce Convertido", 0))
    total = sueldo + bono + bono_rend + diesel + casetas + extras + costo_cruce

    return total

valores = cargar_datos_generales()
st.title("🔁 Simulador de Vuelta Redonda")

if os.path.exists(RUTA_RUTAS):
    df = pd.read_csv(RUTA_RUTAS)
    impo, expo, vacio = df[df["Tipo"]=="IMPO"], df[df["Tipo"]=="EXPO"], df[df["Tipo"]=="VACIO"]

    tipo_principal = st.selectbox("Tipo de ruta principal", ["IMPO", "EXPO"])
    grupo = impo if tipo_principal == "IMPO" else expo
    rutas_opciones = grupo[["Origen", "Destino"]].drop_duplicates().itertuples(index=False, name=None)
    seleccion = st.selectbox("Ruta principal", list(rutas_opciones), format_func=lambda x: f"{x[0]} → {x[1]}")
    origen, destino = seleccion
    candidatas = grupo[(grupo["Origen"] == origen) & (grupo["Destino"] == destino)].copy()

    candidatas["Utilidad"] = candidatas["Ingreso Total"] - candidatas["Costo_Total_Ruta"]
    candidatas["% Utilidad"] = (candidatas["Utilidad"] / candidatas["Ingreso Total"] * 100).round(2)
    candidatas = candidatas.sort_values(by="% Utilidad", ascending=False)
    sel_idx = st.selectbox("Cliente principal", candidatas.index,
                           format_func=lambda x: f"{candidatas.loc[x, 'Cliente']} ({candidatas.loc[x, '% Utilidad']:.2f}%)")
    ruta_principal = candidatas.loc[sel_idx]
    rutas = [ruta_principal]

    # Vacío sugerido
    vacios = vacio[vacio["Origen"] == destino].copy()
    st.markdown("---")
    if not vacios.empty:
        st.subheader("Ruta VACÍA sugerida (opcional)")
        vacio_idx = st.selectbox("Ruta VACÍA", vacios.index,
                                 format_func=lambda x: f"{vacios.loc[x, 'Origen']} → {vacios.loc[x, 'Destino']}")
        ruta_vacio = vacios.loc[vacio_idx]
        rutas.append(ruta_vacio)
        destino = ruta_vacio["Destino"]

    # Secundaria sugerida
    st.markdown("---")
    tipo_sec = "EXPO" if tipo_principal == "IMPO" else "IMPO"
    candidatos = (expo if tipo_principal == "IMPO" else impo)
    sugeridas = candidatos[candidatos["Origen"] == destino].copy()
    if not sugeridas.empty:
        sugeridas["Utilidad"] = sugeridas["Ingreso Total"] - sugeridas["Costo_Total_Ruta"]
        sugeridas["% Utilidad"] = (sugeridas["Utilidad"] / sugeridas["Ingreso Total"] * 100).round(2)
        sugeridas = sugeridas.sort_values(by="% Utilidad", ascending=False)
        idx = st.selectbox("Ruta secundaria sugerida", sugeridas.index,
                           format_func=lambda x: f"{sugeridas.loc[x, 'Cliente']} - {sugeridas.loc[x, 'Origen']} → {sugeridas.loc[x, 'Destino']} ({sugeridas.loc[x, '% Utilidad']:.2f}%)")
        ruta_sec = sugeridas.loc[idx]
        rutas.append(ruta_sec)

    if st.button("🚛 Simular Vuelta Redonda"):
        ingreso_total = sum(safe(r.get("Ingreso Total", 0)) for r in rutas)
        costo_total = sum(calcular_costos(r, valores) for r in rutas)
        utilidad_bruta = ingreso_total - costo_total
        costo_indirecto = ingreso_total * 0.35
        utilidad_neta = utilidad_bruta - costo_indirecto

        st.markdown("---")
        st.subheader("📊 Resultado de Simulación")
        st.metric("Ingreso Total", f"${ingreso_total:,.2f}")
        st.metric("Costo Total", f"${costo_total:,.2f}")
        st.metric("Utilidad Bruta", f"${utilidad_bruta:,.2f}")
        st.metric("Costo Indirecto (35%)", f"${costo_indirecto:,.2f}")
        st.metric("Utilidad Neta", f"${utilidad_neta:,.2f}")
else:
    st.warning("⚠️ No hay rutas cargadas.")
