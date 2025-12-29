import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
import base64
import os
import engine
# Logger is handled via logging module if needed
import random
import time
import plotly.graph_objects as go


# --- 1. CONFIGURACIÓN DE PÁGINA ---
def cargar_configuracion():
    """Establece la configuración base de la página de Streamlit.

    Define el título, el layout ancho y el icono de la aplicación
    para una experiencia táctica coherente.
    """
    st.set_page_config(
        page_title="UrbanOS 2040 Tactical Console", 
        layout="wide", 
        page_icon="icono_u.jpg",
        initial_sidebar_state="expanded"
    )

cargar_configuracion()

# --- 2. GESTIÓN DE RECURSOS ---
@st.cache_data(show_spinner=False)
def get_base64_image_cached(image_path):
    """Codifica una imagen en Base64 con almacenamiento en caché.

    Args:
        image_path (str): Ruta local al archivo de imagen.

    Returns:
        Optional[str]: String codificado en Base64 o None si el archivo no existe.
    """
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- 3. CSS (SENIOR FULLSTACK REFACTOR - MacBook Air M4 Optimized) ---
st.markdown("""
<style>
    /* --- 1. CONFIGURACIÓN GLOBAL (Look Apple Minimalist) --- */
    :root {
        --bg-white: #FFFFFF;
        --text-primary: #000000;
        --text-secondary: #666666;
        --border-color: #E5E5E5;
        --accent-red: #FF3B30;
        --accent-green: #34C759;
        --metro-orange: #FF9500;
        --metro-red: #FF3B30;
        --metro-blue: #007AFF;
        --shadow-soft: 0 4px 24px rgba(0, 0, 0, 0.04);
        --shadow-glass: 0 8px 32px rgba(0, 0, 0, 0.08);
        --font-stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: var(--font-stack) !important;
        background-color: var(--bg-white);
        color: var(--text-primary);
    }

    /* Eliminar Espaciado Lateral Streamlit */
    .block-container {
        padding: 0rem !important;
        max-width: 100% !important;
    }

    /* Ocultar Menú y Footer */
    #MainMenu, footer, header, [data-testid="stHeader"] { visibility: hidden; display: none; }

    /* Sidebar Minimalista */
    [data-testid="stSidebar"] {
        background-color: var(--bg-white) !important;
        border-right: 1px solid var(--border-color) !important;
        min-width: 320px !important;
        padding-top: 0 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 2.5rem 1.5rem !important;
        gap: 0.5rem !important;
    }

    /* Branding */
    .brand-logo {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 24px;
        color: var(--text-primary);
        user-select: none;
    }
    .brand-logo span {
        font-weight: 300;
    }
    .brand-subtitle-new {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-secondary);
        margin-bottom: 32px;
        font-weight: 600;
    }

    /* Sliders & Labels */
    .section-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-secondary);
        margin-top: 24px;
        margin-bottom: 12px;
        font-weight: 600;
    }

    .stSlider label, .stSelectbox label, .stTextInput label { 
        font-size: 12px !important;
        color: var(--text-secondary) !important;
        font-weight: 400 !important;
        text-transform: none !important;
    }

    /* Result Card */
    .result-card {
        background: #F5F5F7;
        border-radius: 12px;
        padding: 20px;
        margin-top: 24px;
    }
    .result-header {
        font-size: 11px;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin-bottom: 12px;
        font-weight: 600;
    }
    .metrics {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }
    .metric-main {
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: var(--text-primary);
    }
    .metric-unit {
        font-size: 14px;
        font-weight: 400;
        color: var(--text-secondary);
        margin-left: 4px;
    }
    .metric-secondary {
        font-size: 14px;
        color: var(--text-secondary);
        text-align: right;
    }

    /* Botones */
    .stButton>button {
        width: 100% !important;
        padding: 12px !important;
        background: #000 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: opacity 0.2s !important;
    }
    .stButton>button:hover {
        opacity: 0.8 !important;
        background: #000 !important;
    }

    /* Top Metrics Bar (Main Area) */
    .metrics-bar {
        position: absolute;
        top: 24px;
        left: 24px;
        right: 24px;
        display: flex;
        gap: 16px;
        z-index: 1000;
        pointer-events: none;
    }
    .glass-metric {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        padding: 12px 20px;
        border-radius: 12px;
        box-shadow: var(--shadow-glass);
        pointer-events: auto;
    }

    /* Leyenda Flotante */
    .legend-widget {
        position: fixed;
        bottom: 32px;
        right: 32px;
        width: 240px;
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 16px;
        padding: 20px;
        box-shadow: var(--shadow-glass);
        z-index: 1000;
    }
    .legend-title {
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 16px;
        color: var(--text-primary);
        border-bottom: 1px solid rgba(0,0,0,0.1);
        padding-bottom: 8px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
        font-size: 12px;
        color: #333;
    }
    .legend-color {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 10px;
    }

    /* Pulse Red Animation */
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
    }
    .marker-pulse-red {
        background: var(--accent-red);
        border-radius: 50%;
        animation: pulse-red 2s infinite;
        width: 12px;
        height: 12px;
        border: 2px solid white;
    }

    /* Quotes */
    .quote-box {
        margin-top: 32px;
        font-size: 11px;
        color: var(--text-secondary);
        font-style: italic;
        line-height: 1.5;
        border-top: 1px solid var(--border-color);
        padding-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. CORE ENGINE INTEGRATION ---

@st.cache_data(show_spinner=False)
def obtener_grafo_optimizado():
    """Recupera el grafo base del motor UrbanOS.

    Returns:
        nx.MultiDiGraph: El grafo urbano cargado y listo para análisis.
    """
    return engine.cargar_grafo_seguro()

@st.cache_data(ttl=300, show_spinner=False)
def get_realtime_sync():
    """Sincroniza datos en tiempo real (Pilar 1: Orquestación).

    Returns:
        Dict: Datos de Ecobici, C5 y telemetría del sistema.
    """
    return engine.fetch_realtime_data()

@st.cache_data(show_spinner=False)
def obtener_analisis_tactico(hurry_factor, c_orig, c_dest, incidentes, realtime_data):
    G = obtener_grafo_optimizado()
    analisis = engine.obtener_analisis_multi_ruta(G, c_orig, c_dest, hurry_factor, incidentes=incidentes, realtime_data=realtime_data)
    
    for key in ["directa", "relampago", "escudo"]:
        if analisis.get(key):
            try:
                # CORRECCIÓN: Usar ox.routing en lugar de ox.utils_graph
                lengths = ox.routing.route_to_gdf(G, analisis[key])["length"]
                distancia_total = sum(lengths)
                analisis[f"{key}_dist"] = distancia_total
                
                # Fallback Táctico: 1.2 m/s (Paso peatonal)
                analisis[f"{key}_time"] = (distancia_total / 1.2) / 60 
            except Exception as e:
                analisis[f"{key}_dist"] = 0
                analisis[f"{key}_time"] = 0
    
    # Misión 9: Integridad y Estrés Urbano
    try:
        if analisis.get("relampago"):
            # Convertimos IDs de nodos a coordenadas para la evaluación de integridad
            ruta_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["relampago"]]
            integridad = engine.evaluar_integridad_ruta(ruta_coords, G=G)
            analisis["integridad"] = integridad
    except Exception as e:
        st.error(f"Error en evaluación de integridad: {e}")
                
    return analisis

def render_gauge_chart(score, level):
    """Crea un gráfico de velocímetro usando Plotly Go."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Estrés Urbano: {level}", 'font': {'size': 14}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': "#0F172A"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#F1F5F9",
            'steps': [
                {'range': [0, 30], 'color': '#10B981'},
                {'range': [30, 70], 'color': '#F59E0B'},
                {'range': [70, 100], 'color': '#EF4444'}],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score}}))
    
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10), font={'family': "Inter"})
    return fig


def render_b2g_analysis(incidentes):
    """Renderiza el análisis de planeación urbana para autoridades (B2G).

    Identifica zonas de intervención basadas en la densidad de incidentes y
    permite sugerir mejoras de infraestructura.

    Args:
        incidentes (List[Dict]): Lista combinada de incidentes reales y sintéticos.
    """
    st.markdown("### Planeación Urbana (B2G)")
    if not incidentes:
        st.write("No hay incidentes reportados en este cuadrante.")
        return
    
    st.write(f"Zonas de Intervención: **{len(incidentes)}**")
    for inc in incidentes:
        with st.expander(f"Incidente: {inc['tipo']}"):
            st.write(f"Prioridad: **ALTA** (Impacto {inc['impacto']}x)")
            st.button(f"Sugerir intervención en coord {list(inc.values())[1:3]}", key=random.random())

COORDENADAS_FIJAS = {
    "Metro Zapata": {"coords": (19.3703, -99.1751), "tipo": "metro"},
    "Metro Centro Médico": {"coords": (19.4072, -99.1545), "tipo": "metro"},
    "Metro Coyoacán": {"coords": (19.3614, -99.1706), "tipo": "metro"},
    "Metro Insurgentes Sur": {"coords": (19.3742, -99.1786), "tipo": "metro"},
    "Ecobici Mixcoac": {"coords": (19.3745, -99.1821), "tipo": "bicicleta"}
}

# --- 5. INITIALIZATION ---

if "rutas_calculadas" not in st.session_state:
    st.session_state["rutas_calculadas"] = False

if "incidentes" not in st.session_state:
    st.session_state["incidentes"] = []

# --- 6. DATA INGESTION (HEARTBEAT) ---
realtime_data = get_realtime_sync()
transporte = engine.extraer_estaciones_transporte()
analisis = {}

if st.session_state["rutas_calculadas"]:
    analisis = obtener_analisis_tactico(
        st.session_state["prisa"], 
        st.session_state["c_orig"], 
        st.session_state["c_dest"],
        st.session_state["incidentes"],
        realtime_data
    )

# --- 7. MAIN INTERFACE (SIDE BAR + DASHBOARD) ---

col_side, col_main = st.columns([0.25, 0.75], gap="small")

with col_side:
    st.markdown('''
    <div class="brand-logo">URBAN<span>graph</span></div>
    <div class="brand-subtitle-new">Plataforma de Análisis Topológico | Ingeniería Mexicana</div>
    ''', unsafe_allow_html=True)

    # 1. Inputs de Ruta
    st.markdown('<div class="section-title">Planificación de Ruta</div>', unsafe_allow_html=True)
    
    opciones = list(COORDENADAS_FIJAS.keys()) + ["-- Manual --"]
    sel_o = st.selectbox("Punto de Inserción", opciones, index=0)
    sel_d = st.selectbox("Objetivo", opciones, index=1)
        
    dir_o = st.text_input("Ingresar Origen (Manual)", "") if sel_o == "-- Manual --" else sel_o
    dir_d = st.text_input("Ingresar Destino (Manual)", "") if sel_d == "-- Manual --" else sel_d
    
    # 2. Sliders Fórmula Sandoval (Dual Linked Sliders)
    st.markdown('<div class="section-title">Fórmula Sandoval</div>', unsafe_allow_html=True)
    
    # Initialize session state for linked sliders
    if "weight_time" not in st.session_state:
        st.session_state.weight_time = 65
        st.session_state.weight_dist = 35

    def update_dist():
        st.session_state.weight_dist = 100 - st.session_state.weight_time
    def update_time():
        st.session_state.weight_time = 100 - st.session_state.weight_dist

    col_t, col_dst = st.columns(2)
    with col_t:
        w_time = st.slider("Peso Tiempo (%)", 0, 100, key="weight_time", on_change=update_dist)
    with col_dst:
        w_dist = st.slider("Peso Distancia (%)", 0, 100, key="weight_dist", on_change=update_time)

    # El hurry_factor para el motor será el peso del tiempo (más peso tiempo = más prisa/menos seguridad)
    st.session_state["prisa"] = w_time

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Actualizar Análisis", type="primary", use_container_width=True):
        with st.spinner("Sincronizando con UrbanOS..."):
            try:
                # Geocoding con Fallback Maestro
                try:
                    c_o = COORDENADAS_FIJAS[dir_o]["coords"] if dir_o in COORDENADAS_FIJAS else engine.geocode_with_cache(f"{dir_o}, CDMX")
                    c_d = COORDENADAS_FIJAS[dir_d]["coords"] if dir_d in COORDENADAS_FIJAS else engine.geocode_with_cache(f"{dir_d}, CDMX")
                except:
                    c_o, c_d = (19.3948, -99.1736), (19.378, -99.178)
                    st.toast("⚠️ Coordenadas de respaldo activadas")

                G = obtener_grafo_optimizado()
                st.session_state["incidentes"] = engine.generar_incidentes_sinteticos(G)
                st.session_state.update({"c_orig": c_o, "c_dest": c_d, "rutas_calculadas": True})
                st.rerun()
            except Exception as e:
                st.error(f"Falla en el motor: {str(e)}")

    # 3. Resultados (Result Card format)
    if st.session_state["rutas_calculadas"]:
        t_relajado = int(analisis.get("relampago_time", 0))
        distancia = int(analisis.get("relampago_dist", 0) or analisis.get("directa_dist", 0))
        eficiencia = 100 - int(analisis.get("integridad", {}).get("urban_stress_percentage", 0))
        
        st.markdown(f'''
        <div class="result-card">
            <div class="result-header">Análisis de Ruta Óptima</div>
            <div class="metrics">
                <div>
                    <span class="metric-main">{t_relajado}</span>
                    <span class="metric-unit">min</span>
                </div>
                <div class="metric-secondary">
                    {distancia} m<br>
                    Eficiencia: {eficiencia}%
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('''
        <div class="quote-box">
            Soli Deo Gloria. Ingeniería al servicio del prójimo. <br>
            Optimizado para Benito Juárez, CDMX.
        </div>
    ''', unsafe_allow_html=True)

with col_main:
    # Top bar is handled within col_main
    pass

with col_main:
    # 1. Floating Top Metrics Bar (Glassmorphism)
    if st.session_state["rutas_calculadas"]:
        t_relajado = int(analisis.get("directa_time", 0))
        m_ganados = int(analisis.get("directa_time", 0) - analisis.get("relampago_time", 0)) if analisis.get("relampago") else 0
        distancia = int(analisis.get("relampago_dist", 0) or analisis.get("directa_dist", 0))
        
        st.markdown(f'''
        <div class="metrics-bar">
            <div class="glass-metric">
                <span style="font-size: 10px; color: var(--text-secondary); text-transform: uppercase;">Tiempo Relajado</span><br>
                <b style="font-size: 18px;">{t_relajado} min</b>
            </div>
            <div class="glass-metric">
                <span style="font-size: 10px; color: var(--text-secondary); text-transform: uppercase;">Ahorro Potencial</span><br>
                <b style="font-size: 18px; color: var(--accent-green);">+{m_ganados} min</b>
            </div>
            <div class="glass-metric">
                <span style="font-size: 10px; color: var(--text-secondary); text-transform: uppercase;">Distancia</span><br>
                <b style="font-size: 18px;">{distancia} m</b>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 2. Map Area (Fixed Height 100vh)
    if not st.session_state["rutas_calculadas"]:
        st.markdown('<div style="display:flex; align-items:center; justify-content:center; background:#F8FAFC; height: 100vh; color:#CBD5E1;"><h2>Defina parámetros de misión para activar cartografía</h2></div>', unsafe_allow_html=True)
    else:
        try:
            m = folium.Map(tiles='CartoDB Positron', attr='UrbanGraph', zoom_start=14, zoom_control=False)
            
            # Draw Paths
            if analisis.get("directa"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["directa"]], color='#000000', weight=2, opacity=0.3, dash_array='5, 5').add_to(m)
            if analisis.get("escudo"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["escudo"]], color='#34C759', weight=4, opacity=0.6).add_to(m)
            if analisis.get("relampago"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["relampago"]], color='#000000', weight=4, opacity=0.9).add_to(m)

            # Custom Marker Icons (SVG)
            def get_svg_icon(type, color):
                if type == 'metro':
                    svg = '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3"/></svg>'
                elif type == 'c5':
                    svg = '<svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
                else: 
                    svg = ''
                
                style = f"background:{color}; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; box-shadow: 0 2px 6px rgba(0,0,0,0.2);"
                if type == 'c5':
                    style += " animation: pulse-red 2s infinite;"
                
                return f'<div style="{style}">{svg}</div>'

            # Markers
            incidents_to_render = st.session_state["incidentes"] + realtime_data.get("incidents", [])
            for inc in incidents_to_render:
                icon_html = get_svg_icon('c5', 'var(--accent-red)')
                folium.Marker([inc["lat"], inc["lon"]], icon=folium.DivIcon(html=icon_html, icon_size=(24,24)), tooltip=inc['tipo']).add_to(m)
            
            for stn in transporte:
                color = 'var(--metro-orange)' if stn['tipo'] == 'Metro' else 'var(--metro-red)'
                icon_html = get_svg_icon('metro', color)
                folium.Marker([stn['lat'], stn['lon']], icon=folium.DivIcon(html=icon_html, icon_size=(20,20)), tooltip=stn['name']).add_to(m)

            m.fit_bounds([st.session_state["c_orig"], st.session_state["c_dest"]], padding=(50, 50))
            st_folium(m, width="100%", height=900, returned_objects=[])

            # Leyenda Táctica Flotante
            st.markdown('''
            <div class="legend-widget">
                <div class="legend-title">Leyenda Táctica</div>
                <div class="legend-item"><div class="legend-color" style="background: var(--metro-orange);"></div><span>Metro (L1, L3, L9)</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--metro-red);"></div><span>Metrobús</span></div>
                <div class="legend-item"><div class="legend-color" style="background: var(--accent-green);"></div><span>Ruta Escudo</span></div>
                <div class="legend-item"><div class="legend-color" style="background: #000;"></div><span>Ruta Relámpago</span></div>
                <div class="legend-item"><div class="marker-pulse-red" style="margin-right:10px;"></div><span>Incidente C5 Activo</span></div>
            </div>
            ''', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Render Error: {e}")





# Fin del archivo UrbanOS 2040 Tactical Console