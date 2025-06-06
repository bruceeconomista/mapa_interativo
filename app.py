import pandas as pd
import folium
from folium.plugins import MarkerCluster
import streamlit as st
from streamlit_folium import st_folium
from io import BytesIO

# --- Carregamento dos dados ---
df_empresas = pd.read_csv("empresas_completas.csv", sep=";", encoding="utf-8")
df_atendidas = pd.read_csv("empresas_atendidas.csv", sep=";", encoding="utf-8")
df_bairros = pd.read_csv("empresas_bairros.csv", sep=";", encoding="utf-8")
df_coords = pd.read_csv("coordenadas_bairros.csv", sep=";", encoding="utf-8", skip_blank_lines=True)

# --- Normalização dos nomes de bairro ---
df_empresas["BAIRRO"] = df_empresas["BAIRRO"].str.upper().str.strip()
df_atendidas["BAIRRO"] = df_atendidas["BAIRRO"].str.upper().str.strip()
df_bairros["Bairro"] = df_bairros["Bairro"].str.upper().str.strip()
df_coords.columns = df_coords.columns.str.strip().str.replace("\ufeff", "")


# --- Identificar empresas não atendidas ---
cnpjs_atendidos = set(df_atendidas["CNPJ"])
df_nao_atendidas = df_empresas[~df_empresas["CNPJ"].isin(cnpjs_atendidos)]

# --- Criar base do mapa com coordenadas ---
print("Colunas de df_coords:", df_coords.columns.tolist())
print("Colunas de df_bairros:", df_bairros.columns.tolist())
df_mapa = df_bairros.merge(df_coords, left_on="Bairro", right_on="Bairro", how="left")

# --- Criar o mapa ---
m = folium.Map(location=[-27.6, -48.5], zoom_start=12)
cluster = MarkerCluster().add_to(m)

for _, row in df_mapa.iterrows():
    bairro = row["Bairro"]
    total = row["Total_Empresas"] - row["Atendidas"]
    lat = row["Latitude"]
    lon = row["Longitude"]

    if pd.notna(lat) and pd.notna(lon):
        folium.Marker(
            location=[lat, lon],
            tooltip=f"{bairro}: {total} não atendidas",
            popup=bairro,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(cluster)

# --- Streamlit Interface ---
st.set_page_config(layout="wide")
st.title("📊 Mapa de Cobertura Comercial")
st.markdown("Clique em um bairro no mapa para ver e baixar os dados das empresas **não atendidas**.")

# Exibir o mapa e capturar clique
st_map = st_folium(m, width=1200, height=600)

# Verificar se o usuário clicou em um bairro
if st_map["last_object_clicked_tooltip"]:
    bairro_selecionado = st_map["last_object_clicked_tooltip"].split(":")[0].strip()
    st.success(f"Bairro selecionado: **{bairro_selecionado}**")

    # Filtrar empresas não atendidas no bairro
    empresas_filtradas = df_nao_atendidas[df_nao_atendidas["BAIRRO"] == bairro_selecionado]

    if not empresas_filtradas.empty:
        st.dataframe(empresas_filtradas)

        # Gerar Excel em memória
        buffer = BytesIO()
        empresas_filtradas.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        # Botão de download
        st.download_button(
            label="📥 Baixar Excel com essas empresas",
            data=buffer,
            file_name=f"empresas_{bairro_selecionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Nenhuma empresa não atendida encontrada nesse bairro.")
