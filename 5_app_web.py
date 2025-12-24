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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Configuración Global de Fuente Look Apple */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #FFFFFF;
    }

    /* Eliminar Espaciado Lateral Streamlit */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* Ocultar Menú y Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}

    /* Sidebar Minimalista */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #F1F5F9 !important;
        box-shadow: none !important;
        min-width: 320px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding: 1.5rem 1rem !important;
    }

    .sidebar-content { 
        background-color: #FFFFFF;
    }

    .header-container { 
        padding-bottom: 12px;
        margin-bottom: 16px;
        border-bottom: 1px solid #F8FAFC;
    }
    .brand-title { 
        font-size: 1.8rem !important; 
        font-weight: 800 !important; 
        color: #000 !important; 
        line-height: 1 !important; 
        margin: 0 !important; 
        letter-spacing: -1.5px !important;
        font-family: 'Inter', sans-serif !important;
        display: block !important;
    }
    .brand-title b { 
        font-weight: 880 !important; 
        color: #000 !important; 
        font-size: 2.1rem !important; 
        display: block !important;
    }
    .brand-subtitle { font-size: 0.55rem; color: #94A3B8; font-weight: 700; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }

    /* Top Metrics Bar */
    .metrics-bar {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background: #FFFFFF;
        padding: 8px 0;
        border-bottom: 1px solid #F1F5F9;
        height: 60px;
    }
    .metric-card {
        text-align: center;
        padding: 0 12px;
        border-right: 1px solid #F1F5F9;
        flex-grow: 1;
    }
    .metric-card:last-child { border-right: none; }
    .metric-label { font-size: 0.55rem; font-weight: 800; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 2px; }
    .metric-value { font-size: 1.2rem; font-weight: 800; color: #0F172A; }
    .metric-value.blue { color: #0EA5E9; }
    .metric-value.green { color: #10B981; }

    /* UI Elements Refinement */
    .stSlider label, .stSelectbox label, .stTextInput label { 
        font-size: 0.65rem !important; 
        font-weight: 700 !important; 
        color: #64748B !important; 
        text-transform: uppercase; 
        margin-bottom: 4px; 
    }
    
    /* Botones Tácticos */
    .stButton>button {
        background-color: #EF4444 !important; /* Rojo Seguridad */
        color: white !important;
        border-radius: 4px !important; /* Esquinas casi rectas */
        height: 42px !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        width: 100% !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #DC2626 !important;
        transform: translateY(-1px);
    }

    .legend-sidebar {
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid #F1F5F9;
    }
    .legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-size: 0.7rem; font-weight: 600; color: #64748B; }
    .legend-icon { font-size: 0.8rem; width: 14px; text-align: center; }

    .status-footer-fixed {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 320px; /* Ancho del sidebar */
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        color: #94A3B8;
        padding: 0 20px;
        height: 32px;
        font-size: 0.6rem;
        font-weight: 700;
        text-transform: uppercase;
        border-top: 1px solid #F1F5F9;
        z-index: 1000;
    }
    .status-dot { width: 6px; height: 6px; background: #10B981; border-radius: 50%; display: inline-block; margin-right: 5px; }
    
    .quote-box {
        margin-top: 20px;
        border-left: 2px solid #F1F5F9;
        padding-left: 12px;
        font-size: 0.65rem;
        color: #94A3B8;
        font-style: italic;
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
                
    return analisis

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
    <div class="header-container">
        <h1 class="brand-title"><b>U</b>RBANgraph</h1>
        <div class="brand-subtitle">Plataforma de Análisis Topológico | Ingeniería Mexicana</div>
    </div>
    
    <div style="font-size: 0.65rem; color: #94A3B8; margin-top: -5px; line-height: 1.3; margin-bottom: 20px; font-weight: 500;">
        Motor de Inteligencia Espacial optimizado para la gestión de riesgos y movilidad urbana.
    </div>
    ''', unsafe_allow_html=True)
    
    opciones = list(COORDENADAS_FIJAS.keys()) + ["-- Manual --"]
    
    col_orig, col_dest = st.columns(2)
    with col_orig:
        sel_o = st.selectbox("Punto de Origen", opciones, index=0)
    with col_dest:
        sel_d = st.selectbox("Punto de Destino", opciones, index=1)
        
    dir_o = st.text_input("Ingresar Origen", "") if sel_o == "-- Manual --" else sel_o
    dir_d = st.text_input("Ingresar Destino", "") if sel_d == "-- Manual --" else sel_d
    
    st.markdown('<br>', unsafe_allow_html=True)
    st.slider("Intensidad de Búsqueda", 0, 100, st.session_state.get("prisa", 50), key="prisa")
    
    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("ANALIZAR RUTA PERSONALIZADA", type="primary", use_container_width=True):
        with st.spinner("Sincronizando con UrbanOS..."):
            try:
                # Geocoding con Fallback Maestro (WTC CDMX / Parque Hundido)
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
                st.error(f"Falla en el motor: {str(e)}") # Muestra el error real para debugging

    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('''
    <div class="legend-sidebar" style="margin-top: 0px; border-top: none;">
        <div class="legend-item"><i class="fa fa-exclamation-triangle legend-icon" style="color:#EF4444"></i> Riesgo C5 (Fatal)</div>
        <div class="legend-item"><div class="legend-icon" style="color:#10B981">●</div> Ruta Escudo (Segura)</div>
        <div class="legend-item"><div class="legend-icon" style="color:#EF4444">●</div> Ruta Relámpago (Veloz)</div>
        <div class="legend-item"><div class="legend-icon" style="color:orange">●</div> Estación Metro</div>
        <div class="legend-item"><i class="fa fa-bicycle legend-icon" style="color:#F59E0B"></i> Red Ecobici</div>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('''
        <div class="quote-box">
            Soli Deo Gloria. Ingeniería al servicio del prójimo. Que el sistema sea limpio y funcional.
        </div>
    ''', unsafe_allow_html=True)
    
    # Persistent Fixed Footer
    st.markdown(f'''
    <div class="status-footer-fixed">
        <div><span class="status-dot"></span> API ONLINE 2.6.0</div>
        <div>UrbanGraph Tactical</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with col_main:
    # Top bar is handled within col_main
    pass

with col_main:
    # 1. Top Metrics Bar - Pure Sans (No Emojis)
    t_relajado = int(analisis.get("directa_time", 0))
    m_ganados = int(analisis.get("directa_time", 0) - analisis.get("relampago_time", 0)) if analisis.get("relampago") else 0
    distancia = int(analisis.get("relampago_dist", 0) or analisis.get("directa_dist", 0))
    
    st.markdown(f'''
    <div class="metrics-bar">
        <div class="metric-card">
            <div class="metric-label">Tiempo Relajado</div>
            <div class="metric-value blue">{t_relajado} min</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Minutos Ganados</div>
            <div class="metric-value green">+{m_ganados}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Distancia Total</div>
            <div class="metric-value">{distancia}m</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 2. Map Area (Fixed Height 700px)
    if not st.session_state["rutas_calculadas"]:
        st.markdown('<div class="map-container" style="display:flex; align-items:center; justify-content:center; background:#FFFFFF; height: 700px; border-radius: 8px; border: 1px solid #F8FAFC;"><h2 style="color:#E2E8F0; font-weight:200;">Parámetros de misión requeridos</h2></div>', unsafe_allow_html=True)
    else:
        try:
            G = obtener_grafo_optimizado()
            m = folium.Map(tiles='CartoDB Positron', attr='UrbanGraph', zoom_start=14)
            
            # Draw Paths
            if analisis.get("directa"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["directa"]], color='#475569', weight=3, opacity=0.2).add_to(m)
            if analisis.get("escudo"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["escudo"]], color='#10B981', weight=5, opacity=0.5).add_to(m)
            if analisis.get("relampago"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["relampago"]], color='#EF4444', weight=6, opacity=0.8).add_to(m)

            # Markers (FontAwesome Professionals)
            incidents_to_render = st.session_state["incidentes"] + realtime_data.get("incidents", [])
            for inc in incidents_to_render:
                folium.Marker([inc["lat"], inc["lon"]], 
                              icon=folium.Icon(color=inc["color"], icon='exclamation-triangle', prefix='fa'), 
                              tooltip=inc['tipo']).add_to(m)
            
            for stn in transporte:
                folium.CircleMarker([stn['lat'], stn['lon']], radius=2, color=stn['color'], fill=True).add_to(m)

            folium.Marker(st.session_state["c_orig"], icon=folium.Icon(color='green', icon='play', prefix='fa'), tooltip="Origen").add_to(m)
            folium.Marker(st.session_state["c_dest"], icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa'), tooltip="Destino").add_to(m)

            m.fit_bounds([st.session_state["c_orig"], st.session_state["c_dest"]], padding=(30, 30))
            st_folium(m, width=None, height=700, returned_objects=[])
        except Exception as e:
            st.error(f"Render Error: {e}")

    # 3. Status Footer
    st.markdown(f'''
    <div class="status-footer" style="display:none;">
    ''', unsafe_allow_html=True)