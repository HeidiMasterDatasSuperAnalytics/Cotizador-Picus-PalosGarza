
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Rutas
RUTA_RUTAS = "rutas_guardadas.csv"
RUTA_PROG = "viajes_programados.csv"
RUTA_DATOS = "datos_generales.csv"

def safe(x): return 0 if pd.isna(x) or x is None else x

def cargar_datos_generales():
    if os.path.exists(RUTA_DATOS):
        return pd.read_csv(RUTA_DATOS).set_index("Parametro").to_dict()["Valor"]
    else:
        return {
            "Rendimiento Camion": 2.5,
            "Costo Diesel": 24.0,
            "Pago x KM (General)": 1.50,
            "Bono ISR IMSS": 462.66,
            "Bono Rendimiento": 250.0,
            "Tipo de cambio USD": 17.5,
            "Tipo de cambio MXN": 1.0
        }

def calcular_costos(tramo, valores):
    km = safe(tramo.get("KM", 0))
    modo = tramo.get("Modo_Viaje", "Operador")
    tipo = tramo.get("Tipo", "IMPO")
    casetas = safe(tramo.get("Casetas", 0))
    pago_km = float(valores.get("Pago x KM (General)", 1.50))
    diesel = (km / float(valores["Rendimiento Camion"])) * float(valores["Costo Diesel"])

    extras = sum([safe(tramo.get(x, 0)) for x in [
        "Movimiento_Local", "Puntualidad", "Pension", "Estancia", "Pistas Extra", 
        "Stop", "Falso", "Gatas", "Accesorios", "Guías"
    ]])

    # Bonos solo si no es VACIO
    bono_isr = float(valores.get("Bono ISR IMSS", 462.66)) if tipo != "VACIO" else 0.0
    bono_rend = float(valores.get("Bono Rendimiento", 250.0)) if tipo != "VACIO" else 0.0

    if modo == "Team":
        sueldo = 1300
        bono = bono_isr * 2
    else:
        sueldo = 100 if tipo == "VACIO" and km < 100 else km * pago_km
        bono = 0 if tipo == "VACIO" else bono_isr

    costo_cruce = safe(tramo.get("Costo Cruce Convertido", 0))
    total = sueldo + bono + bono_rend + diesel + casetas + extras + costo_cruce

    return {
        "Sueldo_Operador": sueldo,
        "Bono": bono,
        "Bono Rendimiento": bono_rend,
        "Costo_Extras": extras,
        "Costo_Diesel_Camion": diesel,
        "Costo_Total_Ruta": total
    }

def asegurar_utilidad(df):
    if "% Utilidad" not in df.columns:
        df["Utilidad"] = df["Ingreso Total"] - df["Costo_Total_Ruta"]
        df["% Utilidad"] = (df["Utilidad"] / df["Ingreso Total"] * 100).round(2)
    return df

st.title("🚚 Programación de Viajes Detallada")
valores = cargar_datos_generales()

def guardar_programacion(df_nueva):
    if os.path.exists(RUTA_PROG):
        df_prog = pd.read_csv(RUTA_PROG)
        df_total = pd.concat([df_prog, df_nueva], ignore_index=True)
    else:
        df_total = df_nueva
    df_total.to_csv(RUTA_PROG, index=False)

def cargar_rutas():
    if not os.path.exists(RUTA_RUTAS):
        st.error("❌ No se encontró rutas_guardadas.csv")
        st.stop()
    df = pd.read_csv(RUTA_RUTAS)
    df["Utilidad"] = df["Ingreso Total"] - df["Costo_Total_Ruta"]
    df["% Utilidad"] = (df["Utilidad"] / df["Ingreso Total"] * 100).round(2)
    df["Ruta"] = df["Origen"] + " → " + df["Destino"]
    return df

# Registro de tráfico
st.header("🚛 Registro de Tráfico - Persona 1")
rutas_df = cargar_rutas()
tipo = st.selectbox("Tipo de ruta (ida)", ["IMPO", "EXPO"])
rutas_tipo = rutas_df[rutas_df["Tipo"] == tipo].copy()

if rutas_tipo.empty:
    st.info("No hay rutas registradas de este tipo.")
    st.stop()

ruta_sel = st.selectbox("Selecciona una ruta", rutas_tipo["Ruta"].unique())
rutas_filtradas = rutas_tipo[rutas_tipo["Ruta"] == ruta_sel].sort_values(by="% Utilidad", ascending=False)

cliente_idx = st.selectbox("Cliente", rutas_filtradas.index,
    format_func=lambda x: f"{rutas_filtradas.loc[x, 'Cliente']} ({rutas_filtradas.loc[x, '% Utilidad']:.2f}%)")
ruta_ida = rutas_filtradas.loc[cliente_idx]

with st.form("registro_trafico"):
    fecha = st.date_input("Fecha de tráfico", value=datetime.today())
    trafico = st.text_input("Número de Tráfico")
    unidad = st.text_input("Unidad")
    operador = st.text_input("Operador")
    submit = st.form_submit_button("📅 Registrar Tráfico")

    if submit:
        if not trafico or not unidad or not operador:
            st.error("❌ Todos los campos son obligatorios para registrar un tráfico.")
        else:
            fecha_str = fecha.strftime("%Y-%m-%d")
            datos = ruta_ida.copy()
            datos["Fecha"] = fecha_str
            datos["Número_Trafico"] = trafico
            datos["Unidad"] = unidad
            datos["Operador"] = operador
            datos["Tramo"] = "IDA"
            datos["ID_Programacion"] = f"{trafico}_{fecha_str}"
            guardar_programacion(pd.DataFrame([datos]))
            st.success("✅ Tráfico registrado exitosamente.")


# Gestión y edición de tráfico
st.markdown("---")
st.header("🛠️ Gestión de Tráficos Programados")

if os.path.exists(RUTA_PROG):
    df_prog = pd.read_csv(RUTA_PROG)
    
    # Filtrar únicamente tráficos incompletos (solo IDA)
    incompletos = df_prog.groupby("ID_Programacion").size().reset_index(name="Tramos")
    incompletos = incompletos[incompletos["Tramos"] == 1]["ID_Programacion"]
    ids = incompletos.tolist()

    if ids:
        id_edit = st.selectbox("Selecciona un tráfico para editar", ids)
        df_filtrado = df_prog[df_prog["ID_Programacion"] == id_edit].reset_index()
        st.write("**Vista previa del tráfico seleccionado:**")
        st.dataframe(df_filtrado)

        if not df_filtrado[df_filtrado["Tramo"] == "IDA"].empty:
            tramo_ida = df_filtrado[df_filtrado["Tramo"] == "IDA"].iloc[0]
            with st.form("editar_trafico"):
                nueva_unidad = st.text_input("Unidad", value=tramo_ida["Unidad"])
                nuevo_operador = st.text_input("Operador", value=tramo_ida["Operador"])

        col1, col2 = st.columns(2)
        with col1:
            movimiento_local = st.number_input("Movimiento Local", min_value=0.0, value=safe(tramo_ida.get("Movimiento_Local", 0)))
            puntualidad = st.number_input("Puntualidad", min_value=0.0, value=safe(tramo_ida.get("Puntualidad", 0)))
            pension = st.number_input("Pensión", min_value=0.0, value=safe(tramo_ida.get("Pension", 0)))
            estancia = st.number_input("Estancia", min_value=0.0, value=safe(tramo_ida.get("Estancia", 0)))
            pistas_extra = st.number_input("Pistas Extra", min_value=0.0, value=safe(tramo_ida.get("Pistas Extra", 0)))
        with col2:
            stop = st.number_input("Stop", min_value=0.0, value=safe(tramo_ida.get("Stop", 0)))
            falso = st.number_input("Falso", min_value=0.0, value=safe(tramo_ida.get("Falso", 0)))
            gatas = st.number_input("Gatas", min_value=0.0, value=safe(tramo_ida.get("Gatas", 0)))
            accesorios = st.number_input("Accesorios", min_value=0.0, value=safe(tramo_ida.get("Accesorios", 0)))
            guias = st.number_input("Guías", min_value=0.0, value=safe(tramo_ida.get("Guías", 0)))

        actualizar = st.form_submit_button("💾 Guardar cambios")
        if actualizar:
            columnas = {
                "Unidad": nueva_unidad,
                "Operador": nuevo_operador,
                "Movimiento_Local": movimiento_local,
                "Puntualidad": puntualidad,
                "Pension": pension,
                "Estancia": estancia,
                "Pistas Extra": pistas_extra,
                "Stop": stop,
                "Falso": falso,
                "Gatas": gatas,
                "Accesorios": accesorios,
                "Guías": guias
            }

            for col, val in columnas.items():
                df_prog.loc[(df_prog["ID_Programacion"] == id_edit) & (df_prog["Tramo"] == "IDA"), col] = val

            # Recalcular costos
            tramo_actualizado = df_prog[(df_prog["ID_Programacion"] == id_edit) & (df_prog["Tramo"] == "IDA")].iloc[0]
            nuevos_costos = calcular_costos(tramo_actualizado, valores)
            for k, v in nuevos_costos.items():
                df_prog.loc[(df_prog["ID_Programacion"] == id_edit) & (df_prog["Tramo"] == "IDA"), k] = v

            df_prog.to_csv(RUTA_PROG, index=False)
            st.success("✅ Cambios guardados correctamente.")


# Simulación de vuelta
st.markdown("---")
st.title("🔁 Simular y Cerrar Tráfico Detallado")

df_prog = pd.read_csv(RUTA_PROG)
df_rutas = pd.read_csv(RUTA_RUTAS)

pendientes = df_prog.groupby("ID_Programacion").size().reset_index(name="count")
pendientes = pendientes[pendientes["count"] == 1]["ID_Programacion"]

if not pendientes.empty:
    id_sel = st.selectbox("Selecciona tráfico pendiente", pendientes)
    ida = df_prog[df_prog["ID_Programacion"] == id_sel].iloc[0]
    destino = ida["Destino"]
    tipo_ida = ida["Tipo"]
    tipo_regreso = "EXPO" if tipo_ida == "IMPO" else "IMPO"

    directas = df_rutas[(df_rutas["Tipo"] == tipo_regreso) & (df_rutas["Origen"] == destino)].copy()
    if not directas.empty:
        directas = directas.sort_values(by="% Utilidad", ascending=False)
        idx = st.selectbox("Cliente sugerido", directas.index,
            format_func=lambda x: f"{directas.loc[x, 'Cliente']} - {directas.loc[x, 'Ruta']} ({directas.loc[x, '% Utilidad']:.2f}%)")
        rutas = [ida, directas.loc[idx]]
    else:
        vacios = df_rutas[(df_rutas["Tipo"] == "VACIO") & (df_rutas["Origen"] == destino)].copy()
        mejor = None
        mejor_utilidad = -99999

        for _, vacio in vacios.iterrows():
            origen_expo = vacio["Destino"]
            expo = df_rutas[(df_rutas["Tipo"] == tipo_regreso) & (df_rutas["Origen"] == origen_expo)]
            expo = asegurar_utilidad(expo)
            if not expo.empty:
                expo = expo.sort_values(by="% Utilidad", ascending=False).iloc[0]
                total_ingreso = sum(safe(x) for x in [ida["Ingreso Total"], vacio["Ingreso Total"], expo["Ingreso Total"]])
                total_costo = sum(safe(x) for x in [ida["Costo_Total_Ruta"], vacio["Costo_Total_Ruta"], expo["Costo_Total_Ruta"]])
                utilidad = total_ingreso - total_costo
                if utilidad > mejor_utilidad:
                    mejor_utilidad = utilidad
                    mejor = (vacio, expo)

        if mejor:
            rutas = [ida, mejor[0], mejor[1]]
        else:
            st.warning("No hay rutas de regreso disponibles.")
            st.stop()

    st.subheader("🧾 Tramos de este tráfico")
    for tramo in rutas:
        st.write(f"{tramo['Tipo']} - {tramo['Origen']} → {tramo['Destino']} | Cliente: {tramo.get('Cliente', 'N/A')}")

    ingreso_total = sum(safe(t["Ingreso Total"]) for t in rutas)
    costo_total = sum(safe(t["Costo_Total_Ruta"]) for t in rutas)
    utilidad_bruta = ingreso_total - costo_total
    costos_indirectos = ingreso_total * 0.35
    utilidad_neta = utilidad_bruta - costos_indirectos

    st.subheader("📊 Resultados")
    st.metric("Ingreso Total", f"${ingreso_total:,.2f}")
    st.metric("Costo Total", f"${costo_total:,.2f}")
    st.metric("Utilidad Bruta", f"${utilidad_bruta:,.2f}")
    st.metric("Costos Indirectos (35%)", f"${costos_indirectos:,.2f}")
    st.metric("Utilidad Neta", f"${utilidad_neta:,.2f}")

    if st.button("💾 Cerrar tráfico"):
        nuevos = []
        for tramo in rutas[1:]:
            tramo["Fecha"] = ida["Fecha"]
            tramo["Número_Trafico"] = ida["Número_Trafico"]
            tramo["Unidad"] = ida["Unidad"]
            tramo["Operador"] = ida["Operador"]
            tramo["ID_Programacion"] = ida["ID_Programacion"]
            tramo["Tramo"] = "VUELTA"
            nuevos.append(tramo)
        guardar_programacion(pd.DataFrame(nuevos))
        st.success("✅ Tráfico cerrado exitosamente.")

# Mostrar Tráficos Concluidos
st.markdown("---")
st.subheader("✅ Tráficos Concluidos")

if os.path.exists(RUTA_PROG):
    df_prog = pd.read_csv(RUTA_PROG)
    concluidos = df_prog.groupby("ID_Programacion").size().reset_index(name="Tramos")
    concluidos = concluidos[concluidos["Tramos"] >= 2]["ID_Programacion"]

    df_concluidos = df_prog[df_prog["ID_Programacion"].isin(concluidos)].copy()

    if not df_concluidos.empty:
        df_concluidos["Fecha"] = pd.to_datetime(df_concluidos["Fecha"])
        st.markdown("### 📅 Filtro por Fecha")
        fecha_inicio = st.date_input("Fecha inicio", value=df_concluidos["Fecha"].min().date())
        fecha_fin = st.date_input("Fecha fin", value=df_concluidos["Fecha"].max().date())

        filtro = (df_concluidos["Fecha"] >= pd.to_datetime(fecha_inicio)) & (df_concluidos["Fecha"] <= pd.to_datetime(fecha_fin))
        df_filtrado = df_concluidos[filtro]

        if not df_filtrado.empty:
            st.dataframe(df_filtrado)
        else:
            st.warning("No hay tráficos concluidos en ese rango de fechas.")
    else:
        st.info("No hay tráficos concluidos todavía.")

