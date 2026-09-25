import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(
    page_title="Mapa Comercial - Siemens",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Siemens e CSS customizado
st.markdown("""
    <style>
    h1, h2, h3 { color: #009999 !important; font-family: 'Arial', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0c1728; }
    
    [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
    [data-testid="stMetricLabel"] { font-size: 11px !important; text-transform: uppercase; color: #8ea2ba !important; }
    div[data-testid="metric-container"] {
        background-color: #101f34;
        border: 1px solid #20314a;
        border-radius: 8px;
        padding: 10px;
    }
    
    .client-list { height: 400px; overflow-y: auto; padding-right: 5px; margin-top: 15px; }
    .client-list::-webkit-scrollbar { width: 6px; }
    .client-list::-webkit-scrollbar-track { background: #0c1728; }
    .client-list::-webkit-scrollbar-thumb { background: #20314a; border-radius: 3px; }
    
    .client-row { padding: 12px 0; border-bottom: 1px solid #20314a; display: flex; gap: 10px; }
    .client-dot { font-size: 16px; line-height: 14px; }
    .client-name { font-size: 12px; color: #eef6ff; font-weight: bold; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .client-meta { font-size: 10px; color: #8ea2ba; }
    </style>
""", unsafe_allow_html=True)

# Nova paleta de cores baseada nos Canais de Vendas
CORES_CANAIS = {
    "Distribuidor": "#00A9E0",        # Azul
    "Integrador": "#F59E0B",          # Laranja
    "OEM": "#EC4899",                 # Rosa
    "Fabricante de Quadro": "#7C3AED",# Roxo
    "Cliente Final": "#10B981"        # Verde
}

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

@st.cache_data
def carregar_dados():
    df = pd.read_excel("lista_clientes_formatada.xlsx")
    if 'Latitude' not in df.columns: df['Latitude'] = None
    if 'Longitude' not in df.columns: df['Longitude'] = None
    if 'Segmento' not in df.columns: df['Segmento'] = "Não informado"
    
    df['CNPJ'] = df['CNPJ'].astype(str)
    df['CEP'] = df['CEP'].astype(str)
    return df

df_base = carregar_dados()

# --- BARRA LATERAL: BUSCA E FILTROS ---
busca_texto = st.sidebar.text_input("Buscar cliente, CNPJ ou CEP", placeholder="Digite aqui...")

vendedores = ["Todos"] + sorted([str(v) for v in df_base['Novo Vendedor'].dropna().unique()])
canais = ["Todos"] + sorted([str(c) for c in df_base['Canal de Vendas'].dropna().unique()])
segmentos = ["Todos"] + sorted([str(s) for s in df_base['Segmento'].dropna().unique()])

vendedor_sel = st.sidebar.selectbox("Vendedor", vendedores)
canal_sel = st.sidebar.selectbox("Canal", canais)
segmento_sel = st.sidebar.selectbox("Segmento", segmentos)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df_base.copy()

if busca_texto:
    busca = busca_texto.lower()
    df_filtrado = df_filtrado[
        df_filtrado['Razão Social'].str.lower().str.contains(busca, na=False) |
        df_filtrado['CNPJ'].str.contains(busca, na=False) |
        df_filtrado['CEP'].str.contains(busca, na=False)
    ]

if vendedor_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Novo Vendedor'] == vendedor_sel]
if canal_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Canal de Vendas'] == canal_sel]
if segmento_sel != "Todos": df_filtrado = df_filtrado[df_filtrado['Segmento'] == segmento_sel]

df_mapeados = df_filtrado.dropna(subset=['Latitude', 'Longitude'])
df_pendentes = df_filtrado[df_filtrado['Latitude'].isna() | df_filtrado['Longitude'].isna()]

# --- MÉTRICAS (3 COLUNAS) ---
col1, col2, col3 = st.sidebar.columns(3)
col1.metric("Clientes", len(df_filtrado))
col2.metric("Pins", len(df_mapeados))
col3.metric("Vendedores", df_filtrado['Novo Vendedor'].nunique())

# --- LISTA ROLÁVEL DE CLIENTES ---
if len(df_filtrado) > 0:
    lista_html = "<div class='client-list'>"
    for _, row in df_filtrado.iterrows():
        canal = str(row.get('Canal de Vendas', ''))
        cor = CORES_CANAIS.get(canal, "#8ea2ba") # Cinza como padrão se não houver match
        
        lista_html += f"""<div class="client-row">
<div class="client-dot" style="color: {cor};">●</div>
<div style="min-width: 0;">
    <div class="client-name" title="{row['Razão Social']}">{row['Razão Social']}</div>
    <div class="client-meta">{row['Canal de Vendas']} • {row['Novo Vendedor']}</div>
</div>
</div>"""
    lista_html += "</div>"
    st.sidebar.markdown(lista_html, unsafe_allow_html=True)

# --- ABAS E MAPA PRINCIPAL ---
tab_mapa, tab_pendentes = st.tabs(["🗺️ Mapa Interativo", "⚠️ Clientes Pendentes de CEP"])

with tab_mapa:
    if len(df_mapeados) == 0:
        st.warning("Nenhum cliente com coordenadas encontradas para o filtro selecionado.")
    else:
        lat_media = df_mapeados['Latitude'].mean()
        lon_media = df_mapeados['Longitude'].mean()

        m = folium.Map(location=[lat_media, lon_media], zoom_start=5, tiles="http://mt0.google.com/vt/lyrs=m&hl=pt-BR&x={x}&y={y}&z={z}", attr="Google Maps")

        for _, row in df_mapeados.iterrows():
            canal = str(row.get('Canal de Vendas', ''))
            cor_hex = CORES_CANAIS.get(canal, "#009999")
            
            popup_html = f"""
            <div style='width: 250px; font-family: Arial, sans-serif;'>
                <b style='color: {cor_hex}; font-size: 14px;'>{row['Razão Social']}</b><br><br>
                <b>CNPJ:</b> {row['CNPJ']}<br>
                <b>Canal:</b> {row['Canal de Vendas']}<br>
                <b>Segmento:</b> {row['Segmento']}<br>
                <b>Vendedor:</b> {row['Novo Vendedor']}<br>
                <b>CEP:</b> {row['CEP']}
            </div>
            """
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['Razão Social'],
                icon=folium.Icon(color='black', icon_color=cor_hex, icon='info-sign')
            ).add_to(m)

        st_folium(m, width=1200, height=620, returned_objects=[])

with tab_pendentes:
    st.subheader(f"Lista de Clientes sem Localização Precisa ({len(df_pendentes)})")
    if len(df_pendentes) > 0:
        colunas_exibicao = ['Razão Social', 'CNPJ', 'CEP', 'Novo Vendedor', 'Canal de Vendas']
        tabela_pendentes = df_pendentes[colunas_exibicao].reset_index(drop=True)
        st.dataframe(tabela_pendentes, use_container_width=True)
        csv_bytes = tabela_pendentes.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(label="📥 Baixar Clientes Pendentes (CSV)", data=csv_bytes, file_name="clientes_pendentes.csv", mime="text/csv")
    else:
        st.success("Todos os clientes filtrados possuem localização no mapa!")