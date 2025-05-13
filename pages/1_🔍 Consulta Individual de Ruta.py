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

st.title("🔍 Consulta Individual de Ruta")

if os.path.exists(RUTA_RUTAS):
    df = pd.read_csv(RUTA_RUTAS)

    st.subheader("📌 Selecciona una Ruta")
    index_sel = st.selectbox(
        "Selecciona índice",
        df.index.tolist(),
        format_func=lambda x: f"{df.loc[x, 'Tipo']} - {df.loc[x, 'Cliente']} - {df.loc[x, 'Origen']} → {df.loc[x, 'Destino']}"
    )

    ruta = df.loc[index_sel]
    tipo = ruta.get("Tipo", "IMPO")
    km = safe_number(ruta.get("KM", 0))
    modo = ruta.get("Modo_Viaje", "Operador")

    # Bonos ajustados
    bono_isr = float(valores.get("Bono ISR IMSS", 462.66)) if tipo != "VACIO" else 0.0
    bono_rend = float(valores.get("Bono Rendimiento", 250.0)) if tipo != "VACIO" else 0.0
    if modo == "Team" and tipo != "VACIO":
        bono_isr *= 2
        bono = bono_isr
    else:
        bono = bono_isr

    # Cálculo de utilidad
    clasificacion = ruta.get("Clasificación Ruta", "RL")
    ingreso_total = safe_number(ruta["Ingreso Total"])
    costo_total = safe_number(ruta["Costo_Total_Ruta"])
    utilidad_bruta = ingreso_total - costo_total
    costos_indirectos = ingreso_total * 0.35
    utilidad_neta = utilidad_bruta - costos_indirectos

    porcentaje_bruta = (utilidad_bruta / ingreso_total * 100) if ingreso_total > 0 else 0
    porcentaje_neta = (utilidad_neta / ingreso_total * 100) if ingreso_total > 0 else 0

    def colored_bold(label, value, condition):
        color = "green" if condition else "red"
        return f"<strong>{label}:</strong> <span style='color:{color}; font-weight:bold'>{value}</span>"

    # =====================
    # 📊 Ingresos y Utilidades
    # =====================
    st.markdown("---")
    st.subheader("📊 Ingresos y Utilidades")

    st.write(f"**Ingreso Total:** ${ingreso_total:,.2f}")
    st.write(f"**Costo Total:** ${costo_total:,.2f}")
    st.markdown(colored_bold("Utilidad Bruta", f"${utilidad_bruta:,.2f}", utilidad_bruta >= 0), unsafe_allow_html=True)
    st.markdown(colored_bold("% Utilidad Bruta", f"{porcentaje_bruta:.2f}%", porcentaje_bruta >= 50), unsafe_allow_html=True)
    st.write(f"**Costos Indirectos (35%):** ${costos_indirectos:,.2f}")
    st.markdown(colored_bold("Utilidad Neta", f"${utilidad_neta:,.2f}", utilidad_neta >= 0), unsafe_allow_html=True)
    st.markdown(colored_bold("% Utilidad Neta", f"{porcentaje_neta:.2f}%", porcentaje_neta >= 15), unsafe_allow_html=True)

    # =====================
    # 📋 Detalles y Costos
    # =====================
    st.markdown("---")
    st.subheader("📋 Detalles y Costos de la Ruta")

    bono_isr = valores.get("Bono ISR IMSS", 462.66)
    bono_rendimiento = valores.get("Bono Rendimiento", 250.0)
    pago_km = valores.get("Pago x KM (General)", 1.50)

    km = safe_number(ruta["KM"])
    if modo_viaje == "Team":
        sueldo = 1300
        bono = bono_isr * 2
    else:
        if ruta["Tipo"] == "VACIO":
            sueldo = 100 if km < 100 else km * pago_km
            bono = 0
        else:
            sueldo = km * pago_km
            bono = bono_isr

    costo_diesel = safe_number(ruta.get("Costo_Diesel_Camion", 0))
    costo_extras = sum(map(safe_number, [
        ruta.get("Movimiento_Local", 0),
        ruta.get("Puntualidad", 0),
        ruta.get("Pension", 0),
        ruta.get("Estancia", 0),
        ruta.get("Pistas Extra", 0),
        ruta.get("Stop", 0),
        ruta.get("Falso", 0),
        ruta.get("Gatas", 0),
        ruta.get("Accesorios", 0),
        ruta.get("Guías", 0)
    ]))

    detalles = [
        f"Fecha: {ruta['Fecha']}",
        f"Tipo: {tipo}",
        f"Modo de viaje: {modo}",
        f"Cliente: {ruta['Cliente']}",
        f"Origen → Destino: {ruta['Origen']} → {ruta['Destino']}",
        f"KM: {km:,.2f}",
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
        f"Bono: ${bono:,.2f}",
        f"Bono Rendimiento: ${bono_rend:,.2f}",
        f"Casetas: ${safe_number(ruta['Casetas']):,.2f}",
        "---",
        "**🧾 Desglose Extras:**",
        f"- Movimiento Local: ${safe_number(ruta['Movimiento_Local']):,.2f}",
        f"- Puntualidad: ${safe_number(ruta['Puntualidad']):,.2f}",
        f"- Pensión: ${safe_number(ruta['Pension']):,.2f}",
        f"- Estancia: ${safe_number(ruta['Estancia']):,.2f}",
        f"- Pistas Extra: ${safe_number(ruta['Pistas Extra']):,.2f}",
        f"- Stop: ${safe_number(ruta['Stop']):,.2f}",
        f"- Falso: ${safe_number(ruta['Falso']):,.2f}",
        f"- Gatas: ${safe_number(ruta['Gatas']):,.2f}",
        f"- Accesorios: ${safe_number(ruta['Accesorios']):,.2f}",
        f"- Guías: ${safe_number(ruta['Guías']):,.2f}"
    ]

    for line in detalles:
        st.write(line)

else:
    st.warning("⚠️ No hay rutas guardadas todavía.")
