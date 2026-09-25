import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Mapa Comercial", layout="wide", initial_sidebar_state="expanded")

# Identidade Visual e Dark Mode
st.markdown("""
    <style>
    h1 { color: #009999; font-family: 'Arial', sans-serif; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #1A1C23; }
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Mapa Comercial de Clientes")

@st.cache_data
def carregar_dados():
    df = pd.read_excel("lista_clientes_formatada.xlsx")
    return df.dropna(subset=['Latitude', 'Longitude'])

df = carregar_dados()

# --- FILTROS (BARRA LATERAL) ---
st.sidebar.markdown("<h3 style='color: #009999;'>Filtros</h3>", unsafe_allow_html=True)

vendedores = ["Todos"] + list(df['Novo Vendedor'].dropna().unique())
canais = ["Todos"] + list(df['Canal de Vendas'].dropna().unique())

vendedor_selecionado = st.sidebar.selectbox("Vendedor", vendedores)
canal_selecionado = st.sidebar.selectbox("Canal de Vendas", canais)

# Aplicação dos Filtros
df_filtrado = df.copy()
if vendedor_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Novo Vendedor'] == vendedor_selecionado]
if canal_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Canal de Vendas'] == canal_selecionado]

# Indicadores Rápidos
st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns(2)
col1.metric("Clientes", len(df_filtrado))
col2.metric("Vendedores", df_filtrado['Novo Vendedor'].nunique())

# --- MAPA (MOTOR GOOGLE MAPS) ---
# tiles puxam diretamente a renderização de mapa do Google
m = folium.Map(
    location=[-8.0475, -34.8770], # Centralizado próximo ao nordeste
    zoom_start=5,
    tiles="http://mt0.google.com/vt/lyrs=m&hl=pt-BR&x={x}&y={y}&z={z}",
    attr="Google Maps"
)

# Renderização dos pinos
for idx, row in df_filtrado.iterrows():
    popup_html = f"""
    <div style='width: 250px; font-family: sans-serif;'>
        <h4 style='color: #009999; margin-bottom: 5px;'>{row['Razão Social']}</h4>
        <b>CNPJ:</b> {row['CNPJ']}<br>
        <b>Canal:</b> {row['Canal de Vendas']}<br>
        <b>Vendedor:</b> {row['Novo Vendedor']}
    </div>
    """
    
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_html, max_width=300),
        tooltip=row['Razão Social'],
        icon=folium.Icon(color='darkblue', icon='info-sign')
    ).add_to(m)

st_folium(m, width=1200, height=600, returned_objects=[])