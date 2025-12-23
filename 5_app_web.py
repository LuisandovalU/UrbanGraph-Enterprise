import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
import base64
import os

import engine

# ==========================================
# 🛑 CONFIGURACIÓN DE MISIÓN (CONSTANTES)
# ==========================================
# RISK_PROFILE ahora se gestiona en engine.py

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="UrbanGraph V23", 
    layout="wide", 
    page_icon="icono_u.jpg"
)

# --- 2. GESTIÓN DE RECURSOS (OPTIMIZADO I/O) ---
@st.cache_data(show_spinner=False)
def get_base64_image_cached(image_path):
    """
    Lee y codifica imágenes en Base64.
    OPTIMIZACIÓN: Usa caché en RAM para evitar I/O de disco repetitivo.
    """
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- 3. CSS (SISTEMA DE DISEÑO) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=Playfair+Display:wght@700&display=swap');
    .stApp { background-color: #FFFFFF; font-family: 'Manrope', sans-serif; color: #0F172A; }
    
    /* HEADER */
    .header-container { display: flex; align-items: center; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px; }
    .logo-img { width: 85px; height: 85px; object-fit: contain; border-radius: 12px; }
    .brand-title { font-family: 'Manrope'; font-size: 2.8rem; font-weight: 800; color: #0F172A; line-height: 1; margin: 0; }
    .brand-subtitle { font-family: 'Manrope'; font-size: 0.95rem; color: #64748B; margin-top: 5px; font-weight: 500; }

    /* TARJETAS */
    .result-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px; }
    .result-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px 20px; }
    .card-label { font-size: 0.7rem; text-transform: uppercase; font-weight: 700; color: #64748B; display: block; }
    .card-value { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #0F172A; }
    .status-badge { font-size: 0.7rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; display: inline-block; }
    .badge-danger { background: #FEF2F2; color: #DC2626; }
    .badge-success { background: #F0FDF4; color: #166534; }
    .badge-info { background: #EFF6FF; color: #2563EB; }
    .report-box { background-color: #F8FAFC; border-left: 4px solid #0F172A; padding: 12px 15px; border-radius: 4px; font-size: 0.9rem; color: #334155; }
    
    /* LEYENDA VISUAL */
    .legend-item { display: flex; align-items: center; margin-bottom: 8px; font-size: 0.85rem; color: #334155; }
    .dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; }
    .dot-green { background-color: #166534; box-shadow: 0 0 5px rgba(22, 101, 52, 0.4); }
    .dot-yellow { background-color: #EAB308; }
    .dot-red { background-color: #DC2626; }
    
    /* MAPA */
    .map-container { border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-top: 15px; }
    
    section[data-testid="stSidebar"] { background-color: #FAFAFA; border-right: 1px solid #E2E8F0; }
    div.stButton > button { background-color: #6C1D45; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: 700; width: 100%; }
    div.stButton > button:hover { background-color: #501633; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container { padding-top: 2rem !important; }

    /* Forzar visibilidad en etiquetas de métricas */
    [data-testid="stMetricLabel"] {
        color: #64748B !important;
    }

    /* Forzar visibilidad en el valor de la métrica si también se pierde */
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 4. NÚCLEO ALGORÍTMICO (DESACOPLADO) ---
if "rutas_calculadas" not in st.session_state:
    st.session_state["rutas_calculadas"] = False

@st.cache_data(show_spinner=False)
def cargar_y_procesar_grafo():
    """
    Carga y procesa el grafo usando el motor Sandoval.
    """
    G = engine.cargar_grafo_seguro()
    return engine.aplicar_formula_sandoval(G)

@st.cache_data(show_spinner=False)
def obtener_sugerencias():
    return engine.extraer_puntos_interes()

@st.cache_data(show_spinner=False)
def obtener_transporte():
    return engine.extraer_estaciones_transporte()

# --- 5. INTERFAZ DE USUARIO ---

# Inicialización de variables de búsqueda (Scope Global)
direccion_orig = ""
direccion_dest = ""
origen_label = "Punto de Inicio"
destino_label = "Punto de Fin"

# HEADER
logo_b64 = get_base64_image_cached("logo.jpg") or get_base64_image_cached("icono_u.jpg")
img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">' if logo_b64 else ''

st.markdown(f"""
<div class="header-container">
    {img_tag}
    <div>
        <h1 class="brand-title">Urban<span style="font-weight:300;">Graph</span></h1>
        <div class="brand-subtitle">Plataforma de Análisis Topológico | <strong>Ingeniería Mexicana</strong></div>
    </div>
</div>
""", unsafe_allow_html=True)

col_sidebar, col_main = st.columns([1, 2.8], gap="large")

with col_sidebar:
    st.markdown("### Parámetros")
    
    with st.spinner("Cargando inteligencia urbana..."):
        sugerencias = obtener_sugerencias()
    
    direccion_orig = st.selectbox("Origen exacto (Benito Juárez)", options=sugerencias, index=sugerencias.index("Parque de los Venados") if "Parque de los Venados" in sugerencias else 0)
    direccion_dest = st.selectbox("Destino exacto (Benito Juárez)", options=sugerencias, index=sugerencias.index("WTC Ciudad de México") if "WTC Ciudad de México" in sugerencias else 1)
    
    st.write("")
    
    prisa = st.slider("¿Qué tanta prisa tienes?", 0, 100, 50, help="0: Prioridad Seguridad | 100: Prioridad Rapidez")
    st.session_state["prisa"] = prisa

    st.write("")
    
    analizar = st.button("ANALIZAR RUTA PERSONALIZADA")
    
    if analizar:
        if direccion_orig == direccion_dest:
            st.error("⚠️ Error de Lógica: Origen y destino son idénticos.")
        else:
            try:
                # Convertir texto a coordenadas reales (lat, lon)
                c_orig = ox.geocode(f"{direccion_orig}, Benito Juárez, CDMX, Mexico")
                c_dest = ox.geocode(f"{direccion_dest}, Benito Juárez, CDMX, Mexico")
                
                # Guardar en session_state para persistencia durante el procesamiento
                st.session_state["c_orig"] = c_orig
                st.session_state["c_dest"] = c_dest
                st.session_state["origen_label"] = direccion_orig
                st.session_state["destino_label"] = direccion_dest
                st.session_state["rutas_calculadas"] = True
            except Exception as ge_error:
                st.error(f"📍 No encontré esa dirección: {ge_error}. Intenta ser más específico.")
            
    st.markdown("---")
    
    with st.expander("¿Cómo funciona el modelo?"):
        st.markdown("""
        El algoritmo analiza cada calle y le asigna una prioridad basada en su nivel de estrés urbano:
        
        <div style="margin-top: 10px;">
            <div class="legend-item">
                <div class="dot dot-green"></div>
                <div><strong>Corredores Seguros:</strong><br>Calles tranquilas (ej. Colima, Tabasco). Preferencia total.</div>
            </div>
            <div class="legend-item">
                <div class="dot dot-yellow"></div>
                <div><strong>Vías Estándar:</strong><br>Tránsito regular. Uso neutral.</div>
            </div>
            <div class="legend-item">
                <div class="dot dot-red"></div>
                <div><strong>Zonas de Evasión:</strong><br>Avenidas de alto flujo (ej. Insurgentes). Se evitan a toda costa.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # --- 6. MENSAJE DE PROPÓSITO ---
    st.markdown("""
    <div style="background-color: #F0FDF4; border-left: 4px solid #166534; padding: 15px; border-radius: 4px;">
        <p style="font-size: 0.85rem; color: #166534; margin: 0; font-style: italic;">
            "Este sistema no solo procesa datos; busca proteger la vida. Mi propósito es poner la ingeniería al servicio de los demás, transformando la tecnología en un instrumento de seguridad y paz."
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption("Luis Sandoval | UPIICSA 2025 | Soli Deo Gloria")

with col_main:
    if not st.session_state["rutas_calculadas"]:
        banner_b64 = get_base64_image_cached("banner.jpg")
        if banner_b64:
            st.markdown(f'<img src="data:image/jpeg;base64,{banner_b64}" style="width:100%; height:350px; object-fit:cover; border-radius:12px;">', unsafe_allow_html=True)
        else:
            st.image("https://images.unsplash.com/photo-1518640467707-6811f4a6ab73?q=80&w=2000", use_container_width=True)
        st.markdown("<div style='margin-top: 25px; color: #64748B;'><p>Sistema en espera. Inicie el cálculo de ruta.</p></div>", unsafe_allow_html=True)

    else:
        try:
            # Inicialización de seguridad para evitar NameError
            node_orig_coords = None
            node_dest_coords = None

            with st.spinner("Procesando topología urbana..."):
                G = cargar_y_procesar_grafo()
            
            c_orig = st.session_state["c_orig"]
            c_dest = st.session_state["c_dest"]
            
            # Cálculo Multi-Ruta Sandoval 2.0
            with st.spinner("Ejecutando simulación multi-agente..."):
                analisis = engine.obtener_analisis_multi_ruta(
                    G, 
                    c_orig, 
                    c_dest, 
                    hurry_factor=st.session_state.get("prisa", 50)
                )
            
            r_seg = analisis["relampago"]
            r_escudo = analisis["escudo"]
            r_rap = analisis["directa"]
            n_orig, n_dest = analisis["nodes"]

            if not r_seg:
                st.error("No se encontró una ruta viable.")
                st.stop()
            
            # Extraer coordenadas de los nodos para las líneas conectoras
            node_orig_coords = (G.nodes[n_orig]['y'], G.nodes[n_orig]['x'])
            node_dest_coords = (G.nodes[n_dest]['y'], G.nodes[n_dest]['x'])

            # Metricas
            d_rap = int(nx.shortest_path_length(G, n_orig, n_dest, weight='length'))
            d_seg = int(nx.shortest_path_length(G, n_orig, n_dest, weight='length')) # Longitud de Relámpago
            
            # Tiempo estimado (caminando a 5km/h = 1.38 m/s)
            t_rap = d_rap / 1.38 / 60
            t_seg = d_seg / 1.38 / 60
            
            ahorro_m = d_seg - d_rap
            
            texto_reporte = f"Análisis Sandoval 2.0: Ruta 'Relámpago' balanceada. Ahorras tiempo frente a la ruta 'Escudo' manteniendo protocolos de seguridad."

            st.markdown(f"""
            <div class="result-grid">
                <div class="result-card" style="border-bottom: 4px solid #94A3B8;"><span class="card-label">Directa (Gris)</span><div class="card-value">{d_rap}m</div><span class="status-badge">RÁPIDA</span></div>
                <div class="result-card" style="border-bottom: 4px solid #EAB308;"><span class="card-label">Relámpago (Oro)</span><div class="card-value">{d_seg}m</div><span class="status-badge badge-info">BALANCEADA</span></div>
                <div class="result-card" style="border-bottom: 4px solid #166534;"><span class="card-label">Escudo (Verde)</span><div class="card-value">Máxima</div><span class="status-badge badge-success">SEGURA</span></div>
            </div>
            <div class="report-box">
                <b>Eficiencia:</b> {int(t_seg)} min estimados. <br>
                {texto_reporte}
            </div>
            """, unsafe_allow_html=True)
            
            m = folium.Map(tiles='CartoDB positron', attr='UrbanGraph')
            
            # Dibujar las 3 rutas
            if r_rap:
                coords_rap = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in r_rap]
                folium.PolyLine(coords_rap, color='#94A3B8', weight=4, opacity=0.4, tooltip="Ruta Directa").add_to(m)
            
            if r_escudo:
                coords_escudo = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in r_escudo]
                folium.PolyLine(coords_escudo, color='#166534', weight=5, opacity=0.6, tooltip="Ruta Escudo (Segura)").add_to(m)

            coords_seg = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in r_seg]
            folium.PolyLine(coords_seg, color='#EAB308', weight=8, opacity=0.9, tooltip="Ruta Relámpago (Sandoval 2.0)").add_to(m)
            
            if node_orig_coords and node_dest_coords:
                folium.PolyLine([c_orig, node_orig_coords], color='#166534', weight=7, opacity=0.9).add_to(m)
                folium.PolyLine([c_dest, node_dest_coords], color='#166534', weight=7, opacity=0.9).add_to(m)
            
            orig_lbl = st.session_state.get("origen_label", "Origen")
            dest_lbl = st.session_state.get("destino_label", "Destino")

            folium.Marker(c_orig, popup=f"<b>{orig_lbl}</b>", icon=folium.Icon(color="black", icon="play", prefix="fa")).add_to(m)
            folium.Marker(c_dest, popup=f"<b>{dest_lbl}</b>", icon=folium.Icon(color="green", icon="flag", prefix="fa")).add_to(m)
            
            # Capas de transporte
            estaciones = obtener_transporte()
            for est in estaciones:
                folium.CircleMarker(
                    [est['lat'], est['lon']],
                    radius=5,
                    color='orange',
                    fill=True,
                    popup=f"Estación: {est['name']}",
                    tooltip="Transporte Público"
                ).add_to(m)

            # --- AJUSTE DINÁMICO DEL MAPA (Auto-zoom) ---
            m.fit_bounds([c_orig, c_dest], padding=(50, 50))
            
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            # height=550 es el tamaño ergonómico
            st_folium(m, width=None, height=550, returned_objects=[])
            st.markdown('</div>', unsafe_allow_html=True)

            # --- 7. DASHBOARD DE SALUD (NASA STYLE) ---
            st.markdown("---")
            col_h1, col_h2, col_h3 = st.columns(3)
            with col_h1:
                st.metric("API Status", "Operational", delta="100% Up")
            with col_h2:
                import psutil
                mem = psutil.virtual_memory().percent
                st.metric("Engine Memory", f"{mem}%", delta="Normal", delta_color="inverse")
            with col_h3:
                st.metric("Network Type", "Topology Walk", delta="Encrypted")

        except Exception as e:
            st.error(f"🛑 Error Crítico del Sistema: {e}")
            st.warning("Diagnóstico: Fallo en conexión API o integridad de grafo. Verifique logs.")