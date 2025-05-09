import streamlit as st
import pandas as pd
import os

RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_DATOS = "datos_generales.csv"

def safe_number(x):
    return 0 if pd.isna(x) or x is None else x

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    else:
        return {}

valores = cargar_datos_generales()

st.title("🔁 Simulador de Vuelta Redonda")

if os.path.exists(RUTA_RUTAS):
    df = pd.read_csv(RUTA_RUTAS)

    impo_rutas = df[df["Tipo"] == "IMPO"].copy()
    expo_rutas = df[df["Tipo"] == "EXPO"].copy()
    vacio_rutas = df[df["Tipo"] == "VACIO"].copy()

    st.subheader("📌 Paso 1: Selecciona tipo de ruta principal")
    tipo_principal = st.selectbox("Tipo principal", ["IMPO", "EXPO"])

    ruta_principal = None
    ruta_vacio = None
    ruta_secundaria = None
    rutas_seleccionadas = []

    if tipo_principal == "IMPO":
        rutas_unicas = impo_rutas[["Origen", "Destino"]].drop_duplicates()
        opciones_ruta = list(rutas_unicas.itertuples(index=False, name=None))
        ruta_sel = st.selectbox("Selecciona ruta IMPO", opciones_ruta, format_func=lambda x: f"{x[0]} → {x[1]}")
        origen, destino = ruta_sel
        candidatas = impo_rutas[(impo_rutas["Origen"] == origen) & (impo_rutas["Destino"] == destino)].copy()
    else:
        rutas_unicas = expo_rutas[["Origen", "Destino"]].drop_duplicates()
        opciones_ruta = list(rutas_unicas.itertuples(index=False, name=None))
        ruta_sel = st.selectbox("Selecciona ruta EXPO", opciones_ruta, format_func=lambda x: f"{x[0]} → {x[1]}")
        origen, destino = ruta_sel
        candidatas = expo_rutas[(expo_rutas["Origen"] == origen) & (expo_rutas["Destino"] == destino)].copy()

    candidatas["Utilidad"] = candidatas["Ingreso Total"] - candidatas["Costo_Total_Ruta"]
    candidatas["% Utilidad"] = (candidatas["Utilidad"] / candidatas["Ingreso Total"] * 100).round(2)
    candidatas = candidatas.sort_values(by="% Utilidad", ascending=False)
    sel = st.selectbox("Cliente (ordenado por % utilidad)", candidatas.index,
                       format_func=lambda x: f"{candidatas.loc[x, 'Cliente']} ({candidatas.loc[x, '% Utilidad']:.2f}%)")
    ruta_principal = candidatas.loc[sel]
    rutas_seleccionadas.append(ruta_principal)

    # Paso 2: sugerencia VACIO
    destino_ref = ruta_principal["Destino"]
    vacios = vacio_rutas[vacio_rutas["Origen"] == destino_ref].copy()
    st.markdown("---")
    st.subheader("📌 Paso 2: Ruta VACÍA sugerida (opcional)")
    if not vacios.empty:
        vacio_idx = st.selectbox("Ruta VACÍA (Origen = " + destino_ref + ")", vacios.index,
                                 format_func=lambda x: f"{vacios.loc[x, 'Origen']} → {vacios.loc[x, 'Destino']}")
        ruta_vacio = vacios.loc[vacio_idx]
        rutas_seleccionadas.append(ruta_vacio)

    # Paso 3: sugerencia secundaria
    st.markdown("---")
    if tipo_principal == "IMPO":
        st.subheader("\ud83d\udccc Paso 3: Ruta EXPO sugerida (opcional)")
        origen_expo = ruta_vacio["Destino"] if ruta_vacio is not None else destino_ref
        candidatos = expo_rutas[expo_rutas["Origen"] == origen_expo].copy()
    else:
        st.subheader("\ud83d\udccc Paso 3: Ruta IMPO sugerida (opcional)")
        origen_impo = ruta_vacio["Destino"] if ruta_vacio is not None else destino_ref
        candidatos = impo_rutas[impo_rutas["Origen"] == origen_impo].copy()

    if not candidatos.empty:
        candidatos["Utilidad"] = candidatos["Ingreso Total"] - candidatos["Costo_Total_Ruta"]
        candidatos["% Utilidad"] = (candidatos["Utilidad"] / candidatos["Ingreso Total"] * 100).round(2)
        candidatos = candidatos.sort_values(by="% Utilidad", ascending=False)
        idx = st.selectbox("Ruta sugerida", candidatos.index,
                           format_func=lambda x: f"{candidatos.loc[x, 'Cliente']} - {candidatos.loc[x, 'Origen']} → {candidatos.loc[x, 'Destino']} ({candidatos.loc[x, '% Utilidad']:.2f}%)")
        ruta_secundaria = candidatos.loc[idx]
        rutas_seleccionadas.append(ruta_secundaria)

    # Simular
    if st.button("🚛 Simular Vuelta Redonda"):
        ingreso_total = sum(safe_number(r.get("Ingreso Total", 0)) for r in rutas_seleccionadas)
        costo_total_general = sum(safe_number(r.get("Costo_Total_Ruta", 0)) for r in rutas_seleccionadas)

        utilidad_bruta = ingreso_total - costo_total_general

        # Obtener el promedio de clasificación de ruta para aplicar el costo indirecto adecuado
        clasificaciones = [r.get("Clasificación Ruta", "RL") for r in rutas_seleccionadas]
        costo_indirecto_total = 0
        for clasif in clasificaciones:
            if clasif == "RC":
                costo_indirecto_total += float(valores.get("Costo Indirecto RC", 7350.44))
            else:
                costo_indirecto_total += float(valores.get("Costo Indirecto RL", 7281.31))

        utilidad_neta = utilidad_bruta - costo_indirecto_total

        pct_bruta = (utilidad_bruta / ingreso_total * 100) if ingreso_total > 0 else 0
        pct_neta = (utilidad_neta / ingreso_total * 100) if ingreso_total > 0 else 0

        st.markdown("---")
        st.markdown("📄 Detalle de Rutas")
        for r in rutas_seleccionadas:
            st.markdown(f"**{r['Tipo']} — {r.get('Cliente', 'N/A')}**")
            st.markdown(f"- {r['Origen']} → {r['Destino']}")
            st.markdown(f"- Clasificación: {r.get('Clasificación Ruta', 'RL')}")
            st.markdown(f"- Modo de viaje: {r.get('Modo_Viaje', 'Operador')}")
            st.markdown(f"- Ingreso Total: ${safe_number(r.get('Ingreso Total')):,.2f}")
            st.markdown(f"- Costo Total Ruta: ${safe_number(r.get('Costo_Total_Ruta')):,.2f}")
            st.markdown("---")

        st.subheader("📊 Resultado General")
        st.markdown(f"**Ingreso Total:** ${ingreso_total:,.2f}")
        st.markdown(f"**Costo Total:** ${costo_total_general:,.2f}")
        st.markdown(f"**Utilidad Bruta:** ${utilidad_bruta:,.2f}")
        st.markdown(f"**% Utilidad Bruta:** {pct_bruta:.2f}%")
        st.markdown(f"**Costos Indirectos Totales:** ${costo_indirecto_total:,.2f}")
        st.markdown(f"**Utilidad Neta:** ${utilidad_neta:,.2f}")
        st.markdown(f"**% Utilidad Neta:** {pct_neta:.2f}%")
else:
    st.warning("⚠️ No hay rutas guardadas todavía.")
