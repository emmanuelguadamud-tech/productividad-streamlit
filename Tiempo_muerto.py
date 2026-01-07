import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# ---------------- CONFIGURACIÓN ----------------
JORNADA_INICIO = time(8, 0)
JORNADA_FIN = time(14, 30)

HORAS_JORNADA = (
    datetime.combine(datetime.today(), JORNADA_FIN)
    - datetime.combine(datetime.today(), JORNADA_INICIO)
).seconds / 3600

st.set_page_config(page_title="Productividad", layout="wide")

# ---------------- USUARIO ----------------
st.sidebar.title("👤 Usuario")
usuario = st.sidebar.text_input("Nombre de usuario")

if not usuario:
    st.warning("Ingresa tu nombre para comenzar")
    st.stop()

ARCHIVO = f"actividades_{usuario.lower()}.csv"

# ---------------- CARGAR DATOS ----------------
if os.path.exists(ARCHIVO):
    df = pd.read_csv(ARCHIVO)
else:
    df = pd.DataFrame(
        columns=["Fecha", "Inicio", "Fin", "Duración", "Categoría", "Descripción"]
    )

# Conversión robusta de fechas
if not df.empty:
    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce",
        format="mixed"
    )
    df = df.dropna(subset=["Fecha"])
    df = df.sort_values("Fecha", ascending=False)  # 🔥 VER LO MÁS RECIENTE ARRIBA

# ---------------- TÍTULO ----------------
st.title("📅 Control personal de productividad")

# ---------------- REGISTRO ----------------
st.subheader("➕ Registrar actividad")

with st.form("form_actividad", clear_on_submit=True):
    fecha = st.date_input("Fecha", datetime.today())
    inicio = st.time_input("Hora inicio", JORNADA_INICIO)
    fin = st.time_input("Hora fin", JORNADA_FIN)
    categoria = st.selectbox("Categoría", ["Oficina", "Campo"])
    descripcion = st.text_input("Descripción")

    guardar = st.form_submit_button("Guardar actividad")

    if guardar:
        if fin <= inicio:
            st.error("La hora fin debe ser mayor a la hora inicio")
        else:
            duracion = (
                datetime.combine(fecha, fin)
                - datetime.combine(fecha, inicio)
            ).seconds / 3600

            nueva = pd.DataFrame([{
                "Fecha": fecha,
                "Inicio": inicio.strftime("%H:%M"),
                "Fin": fin.strftime("%H:%M"),
                "Duración": duracion,
                "Categoría": categoria,
                "Descripción": descripcion
            }])

            df = pd.concat([df, nueva], ignore_index=True)
            df.to_csv(ARCHIVO, index=False)

            st.success("Actividad guardada correctamente")
            st.rerun()

# ---------------- FILTROS ----------------
st.divider()
st.subheader("📆 Filtros")

if not df.empty:
    # ---- Filtro por mes ----
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)
    meses = sorted(df["Mes"].unique())

    meses_seleccionados = st.multiselect(
        "Selecciona uno o varios meses",
        meses,
        default=meses  # ✅ TODOS LOS MESES POR DEFECTO
    )

    df_filtrado = df[df["Mes"].isin(meses_seleccionados)]

    # ---- Filtro por día ----
    dias_disponibles = sorted(df_filtrado["Fecha"].dt.date.unique())

    dias_seleccionados = st.multiselect(
        "Selecciona uno o varios días",
        dias_disponibles
    )

    if dias_seleccionados:
        df_filtrado = df_filtrado[
            df_filtrado["Fecha"].dt.date.isin(dias_seleccionados)
        ]
else:
    df_filtrado = df

# ---------------- TABLA ----------------
st.divider()
st.subheader("📋 Actividades registradas")

if df_filtrado.empty:
    st.info("No hay actividades para los filtros seleccionados")
else:
    st.dataframe(df_filtrado, use_container_width=True)

# ---------------- ELIMINAR UNA FILA ----------------
st.subheader("🗑️ Eliminar actividad puntual")

if not df_filtrado.empty:
    fila = st.selectbox(
        "Selecciona la actividad a eliminar",
        df_filtrado.index,
        format_func=lambda i: (
            f"{df.loc[i,'Fecha'].date()} | "
            f"{df.loc[i,'Inicio']}–{df.loc[i,'Fin']} | "
            f"{df.loc[i,'Categoría']}"
        )
    )

    if st.button("Eliminar actividad"):
        df = df.drop(index=fila).reset_index(drop=True)
        df.to_csv(ARCHIVO, index=False)
        st.success("Actividad eliminada")
        st.rerun()

# ---------------- RESUMEN ----------------
st.divider()
st.subheader("📊 Resumen según filtros")

if not df_filtrado.empty:
    oficina = df_filtrado[df_filtrado["Categoría"] == "Oficina"]["Duración"].sum()
    campo = df_filtrado[df_filtrado["Categoría"] == "Campo"]["Duración"].sum()
    ocupado = oficina + campo

    dias_trabajados = df_filtrado["Fecha"].dt.date.nunique()
    horas_teoricas = dias_trabajados * HORAS_JORNADA
    tiempo_muerto = max(0, horas_teoricas - ocupado)

    c1, c2, c3 = st.columns(3)
    c1.metric("🏢 Oficina", f"{oficina:.2f} h")
    c2.metric("🌱 Campo", f"{campo:.2f} h")
    c3.metric("⏱️ Tiempo muerto", f"{tiempo_muerto:.2f} h")

    st.caption(
        f"Días trabajados: {dias_trabajados} | "
        f"Horas teóricas: {horas_teoricas:.2f} h"
    )
