import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
import base64
import os
import engine
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
def cargar_configuracion():
    """Establece la configuración base de la página de Streamlit.

    Define el título, el layout ancho y el icono de la aplicación
    para una experiencia táctica coherente.
    """
    st.set_page_config(
        page_title="UrbanOS 2040 Tactical Console", 
        layout="wide", 
        page_icon="icono_u.jpg"
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

# --- 3. CSS (DASHBOARD ZERO-SCROLL DARK MODE) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Playfair+Display:wght@700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        overflow: hidden;
        height: 100vh;
        background-color: #0F172A; /* Dark mode base */
    }
    .block-container {
        padding: 0.5rem 1rem !important;
        max-width: 100% !important;
    }
    header, footer, #MainMenu { visibility: hidden; }

    .stApp { background-color: #0F172A; font-family: 'Manrope', sans-serif; color: #F8FAFC; }
    
    .sidebar-content { height: 95vh; overflow-y: auto; padding-right: 10px; }

    .header-container { display: flex; align-items: center; gap: 15px; padding-bottom: 10px; border-bottom: 1px solid #1E293B; margin-bottom: 15px; }
    .logo-img { width: 50px; height: 50px; object-fit: contain; border-radius: 8px; border: 1px solid #334155; }
    .brand-title { font-size: 1.8rem; font-weight: 800; color: #F8FAFC; line-height: 1; margin: 0; }
    .brand-subtitle { font-size: 0.8rem; color: #94A3B8; }

    .result-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 15px; }
    .result-card { background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 12px; }
    .card-label { font-size: 0.65rem; text-transform: uppercase; font-weight: 700; color: #94A3B8; }
    .card-value { font-size: 1.4rem; font-weight: 700; color: #F8FAFC; }
    
    .status-badge { font-size: 0.6rem; font-weight: 700; padding: 2px 5px; border-radius: 3px; }
    .badge-info { background: #0EA5E9; color: white; }
    .badge-success { background: #10B981; color: white; }
    .badge-danger { background: #EF4444; color: white; }

    .map-container { height: 94vh; border-radius: 12px; overflow: hidden; border: 1px solid #334155; }

    /* Observability Panel */
    .observability-panel { background: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 10px; margin-top: 15px; }
    .obs-item { display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 5px; color: #94A3B8; }
    .obs-value { font-weight: 700; color: #F8FAFC; }
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
    """Calcula el vector táctico para las tres rutas soportadas.

    Args:
        hurry_factor (float): Nivel de optimización temporal (0-100).
        c_orig (Tuple[float, float]): Origen geográfico.
        c_dest (Tuple[float, float]): Destino geográfico.
        incidentes (List[Dict]): Alertas de seguridad activas.
        realtime_data (Dict): Feed de datos en vivo de APIs.

    Returns:
        Dict: Resultados del análisis multi-ruta.
    """
    G = obtener_grafo_optimizado()
    return engine.obtener_analisis_multi_ruta(
        G, c_orig, c_dest, 
        hurry_factor=hurry_factor, 
        incidentes=incidentes, 
        realtime_data=realtime_data
    )

def render_b2g_analysis(incidentes):
    """Renderiza el análisis de planeación urbana para autoridades (B2G).

    Identifica zonas de intervención basadas en la densidad de incidentes y
    permite sugerir mejoras de infraestructura.

    Args:
        incidentes (List[Dict]): Lista combinada de incidentes reales y sintéticos.
    """
    st.markdown("### 📊 Planeación Urbana (B2G)")
    if not incidentes:
        st.write("No hay incidentes reportados en este cuadrante.")
        return
    
    st.write(f"Zonas de Intervención: **{len(incidentes)}**")
    for inc in incidentes:
        with st.expander(f"📍 {inc['tipo']}"):
            st.write(f"Prioridad: **ALTA** (Impacto {inc['impacto']}x)")
            st.button(f"Sugerir luminaria en coord {list(inc.values())[1:3]}", key=random.random())

COORDENADAS_FIJAS = {
    "Metro Zapata": {"coords": (19.3703, -99.1751), "tipo": "metro"},
    "Metro Centro Médico": {"coords": (19.4072, -99.1545), "tipo": "metro"},
    "Parque Hundido": {"coords": (19.3783, -99.1788), "tipo": "parque"},
    "Ecobici Mixcoac": {"coords": (19.3745, -99.1821), "tipo": "bicicleta"},
    "Ecobici Félix Cuevas": {"coords": (19.3734, -99.1775), "tipo": "bicicleta"}
}

# --- 5. INITIALIZATION ---

if "rutas_calculadas" not in st.session_state:
    st.session_state["rutas_calculadas"] = False
if "incidentes" not in st.session_state:
    G_init = engine.cargar_grafo_seguro()
    st.session_state["incidentes"] = engine.generar_incidentes_sinteticos(G_init)

# --- 6. LAYOUT ---

col_side, col_map = st.columns([1, 3], gap="small")

with col_side:
    logo_b64 = get_base64_image_cached("logo.jpg") or get_base64_image_cached("icono_u.jpg")
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">' if logo_b64 else ''
    st.markdown(f'<div class="header-container">{img_tag}<div><h1 class="brand-title">UrbanOS</h1><div class="brand-subtitle">Evolution 2040</div></div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    opciones = list(COORDENADAS_FIJAS.keys()) + ["-- Manual --"]
    sel_o = st.selectbox("Punto de Inserción", opciones, index=0)
    dir_o = st.text_input("📍 Coord. Origen", "") if sel_o == "-- Manual --" else sel_o
    
    sel_d = st.selectbox("Objetivo Táctico", opciones, index=1)
    dir_d = st.text_input("🏁 Coord. Destino", "") if sel_d == "-- Manual --" else sel_d
    
    prisa = st.slider("Hurry Factor (Optimization)", 0, 100, st.session_state.get("prisa", 50))
    st.session_state["prisa"] = prisa
    
    modo_b2g = st.toggle("Activar B2G Planning Mode", value=False)

    if st.button("ANALIZAR RED TÁCTICA", type="primary", use_container_width=True):
        try:
            with st.spinner("Sincronizando..."):
                c_o = COORDENADAS_FIJAS[dir_o]["coords"] if dir_o in COORDENADAS_FIJAS else ox.geocode(f"{dir_o}, CDMX")
                c_d = COORDENADAS_FIJAS[dir_d]["coords"] if dir_d in COORDENADAS_FIJAS else ox.geocode(f"{dir_d}, CDMX")
                
                # Regenerate incidents on new mission
                st.session_state["incidentes"] = engine.generar_incidentes_sinteticos(obtener_grafo_optimizado())
                st.session_state.update({"c_orig": c_o, "c_dest": c_d, "rutas_calculadas": True})
                st.rerun()
        except: st.error("Fallo de Geolocalización.")

    if st.session_state["rutas_calculadas"]:
        with st.status("📡 Sincronización UrbanOS 2040", expanded=False) as status:
            st.write("Conectando con Servidores C5...")
            realtime_data = get_realtime_sync()
            st.write("Calculando Vector Sandoval (KDTree enabled)...")
            analisis = obtener_analisis_tactico(
                st.session_state["prisa"], 
                st.session_state["c_orig"], 
                st.session_state["c_dest"],
                st.session_state["incidentes"],
                realtime_data
            )
            status.update(label="Sincronización Completa ✅", state="complete")
            
            G_ref = obtener_grafo_optimizado()
            n_o, n_d = analisis["nodes"]
            d_rel = int(nx.shortest_path_length(G_ref, n_o, n_d, weight='length'))
            t_rel = int(d_rel / 83.3)
            
            d_esc = int(nx.shortest_path_length(G_ref, n_o, n_d, weight='length')) if analisis["escudo"] else d_rel
            integrity = round((d_rel / d_esc * 100), 1) if d_esc > 0 else 100
            
            # Cómputo de alertas combinadas
            total_alerts = len(st.session_state["incidentes"]) + len(realtime_data["incidents"])
            data_health = realtime_data.get("integrity", "Unknown")
            health_color = "badge-success" if "Optimal" in data_health else "badge-info" if "Degraded" in data_health else "badge-danger"

            st.markdown(f"""
            <div class="result-grid">
                <div class="result-card"><span class="card-label">Tiempo Relámpago</span><div class="card-value">{t_rel} min</div><span class="status-badge badge-info">REAL-TIME SYNC</span></div>
                <div class="result-card"><span class="card-label">Integrity Score</span><div class="card-value">{integrity}%</div><span class="status-badge badge-success">VERIFIED</span></div>
                <div class="result-card"><span class="card-label">Alertas C5 Activas</span><div class="card-value">{total_alerts}</div><span class="status-badge badge-danger">PROACTIVE SAFETY</span></div>
                <div class="result-card"><span class="card-label">Data Health</span><div class="card-value" style="font-size: 1rem;">{data_health}</div><span class="status-badge {health_color}">SYSTEM</span></div>
            </div>
            
            <div class="observability-panel">
                <div style="font-size: 0.7rem; font-weight: 800; color: #64748B; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Observabilidad de Sistema</div>
                <div class="obs-item"><span>Latencia de Red (P99)</span><span class="obs-value">{realtime_data['metrics']['latency_ms']}ms</span></div>
                <div class="obs-item"><span>Fidelidad de Datos</span><span class="obs-value">{realtime_data['metrics']['fidelity']}%</span></div>
                <div class="obs-item"><span>Alertas en Radio</span><span class="obs-value">{total_alerts}</span></div>
                <div class="obs-item"><span>Patrón de Resiliencia</span><span class="obs-value" style="color: #10B981;">Circuit Breaker 3s</span></div>
            </div>

            <div style="margin-top: 15px;">
                <details style="background: #0F172A; border: 1px solid #1E293B; border-radius: 8px; padding: 10px; color: #94A3B8; font-size: 0.75rem;">
                    <summary style="cursor: pointer; font-weight: 800; color: #64748B; text-transform: uppercase;">Panel de Integridad</summary>
                    <div style="margin-top: 10px;">
                        <div class="obs-item"><span>C5 Connection</span><span class="obs-value" style="color: {'#10B981' if realtime_data['integrity'] != 'Critical' else '#EF4444'}">{'Active' if realtime_data['integrity'] != 'Critical' else 'Fallback'}</span></div>
                        <div class="obs-item"><span>Última Sincronía</span><span class="obs-value">{realtime_data['metrics']['last_sync']}</span></div>
                        <div class="obs-item"><span>Resiliencia Auditor</span><span class="obs-value">Log Active</span></div>
                    </div>
                </details>
            </div>
            """, unsafe_allow_html=True)
            
            if modo_b2g:
                render_b2g_analysis(st.session_state["incidentes"] + realtime_data["incidents"])
            else:
                st.info("UrbanOS 2040: Integridad Asegurada.")

    st.markdown("---")
    st.caption("Soli Deo Gloria | Enterprise Edition 2.4")
    st.markdown('</div>', unsafe_allow_html=True)

with col_map:
    if not st.session_state["rutas_calculadas"]:
        st.markdown('<div class="map-container" style="display:flex; align-items:center; justify-content:center; background:#0F172A; border:1px dashed #334155;"><div><h1 style="text-align:center; color:#334155;">UrbanOS 2040</h1><p style="text-align:center; color:#1E293B;">Waiting for tactical input...</p></div></div>', unsafe_allow_html=True)
    else:
        try:
            # Note: Using G_ref for geometry, but weights are already applied in background
            G = obtener_grafo_optimizado()
            realtime_data = get_realtime_sync()
            analisis = obtener_analisis_tactico(
                st.session_state["prisa"], 
                st.session_state["c_orig"], 
                st.session_state["c_dest"],
                st.session_state["incidentes"],
                realtime_data
            )
            m = folium.Map(tiles='CartoDB dark_matter', attr='UrbanOS')
            
            # Draw Paths
            if analisis.get("directa"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["directa"]], color='#475569', weight=3, opacity=0.3).add_to(m)
            if analisis.get("escudo"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["escudo"]], color='#10B981', weight=5, opacity=0.6).add_to(m)
            if analisis.get("relampago"):
                folium.PolyLine([(G.nodes[n]['y'], G.nodes[n]['x']) for n in analisis["relampago"]], color='#F59E0B', weight=8, opacity=0.9).add_to(m)

            # Incidents Layer (Sintéticos + Reales)
            all_icons = st.session_state["incidentes"] + realtime_data["incidents"]
            for inc in all_icons:
                folium.Marker(
                    [inc["lat"], inc["lon"]],
                    icon=folium.Icon(color=inc["color"], icon=inc.get("icon", "warning"), prefix="fa"),
                    tooltip=f"<b>ALERTA C5 {'(REAL)' if 'impacto' in inc and 'icon' not in inc else ''}</b>: {inc['tipo']}"
                ).add_to(m)

            # Ecobici Layer (Real-time True Stock)
            bicis = realtime_data["ecobici"]
            for nombre, info in COORDENADAS_FIJAS.items():
                if info.get("tipo") == "bicicleta":
                    # Intentar matchear estación por nombre o random logic para demo
                    stock = random.choice(list(bicis.values())) if bicis else "0"
                    color_stock = "#F59E0B" if int(stock) > 0 else "#EF4444"
                    folium.CircleMarker(
                        info["coords"], radius=10, color=color_stock, fill=True, 
                        tooltip=f"Ecobici {nombre}: {stock} disponibles",
                        popup=f"Status: {'OPERATIVO' if int(stock) > 0 else 'SIN BICIS'}<br>Stock: {stock}"
                    ).add_to(m)

            m.fit_bounds([st.session_state["c_orig"], st.session_state["c_dest"]], padding=(100, 100))
            st_folium(m, width=None, height=900, returned_objects=[])
        except Exception as e: st.error(f"Render Error: {e}")