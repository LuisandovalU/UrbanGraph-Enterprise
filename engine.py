import osmnx as ox
import networkx as nx

# Configuración profesional del caché (Sustituye al decorador antiguo)
ox.settings.use_cache = True
ox.settings.cache_folder = "./cache"

# Configuración del Perfil de Riesgo (Fórmula Sandoval)
RISK_PROFILE = {
    "WEIGHTS": {
        "SAFE": 1.0,      # Corredores Verdes
        "STANDARD": 10.0, # Calles Normales
        "DANGER": 50.0    # Avenidas de Alto Estrés
    },
    "KEYWORDS": {
        "SAFE": ["colima", "tabasco", "guadalajara", "orizaba", "chiapas", "jalapa"],
        "DANGER": ["insurgentes", "alvaro obregon", "durango", "chapultepec", "sonora"]
    },
    "LOCATION": "Benito Juárez, Ciudad de México, Mexico"
}

def cargar_grafo_seguro():
    """Descarga y prepara el grafo base."""
    ox.settings.useful_tags_way = ['name', 'highway', 'length']
    return ox.graph_from_place(RISK_PROFILE["LOCATION"], network_type="walk")

def aplicar_formula_sandoval(G, weather_impact=1.0, hurry_factor=50.0):
    """
    Aplica la Función de Costo Generalizado Sandoval 2.0.
    hurry_factor: 0 (Seguridad Total) a 100 (Rapidez Total).
    """
    h_ratio = hurry_factor / 100.0
    s_ratio = 1.0 - h_ratio

    for u, v, k, data in G.edges(keys=True, data=True):
        segment_length = data.get('length', 10.0)
        street_name = str(data.get('name', '')).lower()
        
        # Lógica de riesgo base
        risk_multiplier = RISK_PROFILE["WEIGHTS"]["STANDARD"]
        
        if any(safe_key in street_name for safe_key in RISK_PROFILE["KEYWORDS"]["SAFE"]):
            risk_multiplier = RISK_PROFILE["WEIGHTS"]["SAFE"]
            
        if any(danger_key in street_name for danger_key in RISK_PROFILE["KEYWORDS"]["DANGER"]):
            risk_multiplier = RISK_PROFILE["WEIGHTS"]["DANGER"]
            
        # AUDACIA SANDOVAL: Reducir intensidad del riesgo si hay prisa
        # Si h_ratio=1.0 (prisa máx), el multiplicador de riesgo tiende a 1.0 (neutral)
        impacto_riesgo = 1.0 + (risk_multiplier - 1.0) * s_ratio
        
        # Fórmula Sandoval 2.1: Balance dinámico
        data['final_impedance'] = (segment_length * h_ratio) + (segment_length * impacto_riesgo * weather_impact * s_ratio)
        
    return G

def calcular_ruta_optima(G, coords_orig, coords_dest, criterio='final_impedance'):
    """Calcula la ruta usando el motor de pesos Sandoval."""
    n_orig = ox.nearest_nodes(G, coords_orig[1], coords_orig[0])
    n_dest = ox.nearest_nodes(G, coords_dest[1], coords_dest[0])
    
    try:
        ruta = nx.shortest_path(G, n_orig, n_dest, weight=criterio)
        return ruta, n_orig, n_dest
    except nx.NetworkXNoPath:
        return None, n_orig, n_dest

def obtener_analisis_multi_ruta(G, coords_orig, coords_dest, hurry_factor=50.0, weather_impact=1.0):
    """Calcula simultáneamente las tres rutas: Escudo, Relámpago y Directa."""
    # 1. Ruta Directa (Rapidez Pura)
    r_directa, n_orig, n_dest = calcular_ruta_optima(G, coords_orig, coords_dest, criterio='length')
    
    # 2. Ruta Escudo (Seguridad Total - prisa 0)
    G_escudo = aplicar_formula_sandoval(G.copy(), weather_impact=weather_impact, hurry_factor=0)
    r_escudo, _, _ = calcular_ruta_optima(G_escudo, coords_orig, coords_dest)
    
    # 3. Ruta Relámpago (Balanceada - según slider)
    G_relampago = aplicar_formula_sandoval(G.copy(), weather_impact=weather_impact, hurry_factor=hurry_factor)
    r_relampago, _, _ = calcular_ruta_optima(G_relampago, coords_orig, coords_dest)
    
    return {
        "escudo": r_escudo,
        "relampago": r_relampago,
        "directa": r_directa,
        "nodes": (n_orig, n_dest)
    }

def extraer_puntos_interes(location=RISK_PROFILE["LOCATION"]):
    """Extrae nombres de calles y lugares clave para auto-completado."""
    try:
        # Obtener etiquetas de calles
        G = cargar_grafo_seguro()
        nombres_calles = set()
        for u, v, data in G.edges(data=True):
            if 'name' in data:
                if isinstance(data['name'], list):
                    nombres_calles.update(data['name'])
                else:
                    nombres_calles.add(data['name'])
        
        # Obtener POIs (Parques, Plazas, Iglesias)
        tags = {
            'leisure': ['park', 'garden'], 
            'amenity': ['place_of_worship', 'library', 'cafe'],
            'landuse': ['religious']
        }
        pois = ox.features_from_place(location, tags)
        nombres_pois = []
        if not pois.empty and 'name' in pois.columns:
            nombres_pois = pois['name'].dropna().unique().tolist()
        
        return sorted(list(nombres_calles) + nombres_pois)
    except Exception as e:
        print(f"Error extrayendo POIs: {e}")
        return ["Parque de los Venados", "WTC Ciudad de México", "Metro Zapata", "Metro Centro Médico"]

def extraer_estaciones_transporte(location=RISK_PROFILE["LOCATION"]):
    """Busca y categoriza estaciones de transporte (Metro, Metrobús, Trolebús)."""
    tags = {
        'public_transport': ['station', 'stop_position'],
        'railway': ['station', 'subway_entrance'],
        'amenity': ['bus_station']
    }
    try:
        stations = ox.features_from_place(location, tags)
        if stations.empty:
            return []
        
        results = []
        for _, row in stations.iterrows():
            name = row.get('name', '')
            if not name or str(name) == 'nan': continue
            
            # Lógica de categorización por tags de OSM
            tipo = "Autobús"
            color = "gray"
            
            if any(x in str(row).lower() for x in ['subway', 'metro', 'linea 3', 'linea 12']):
                tipo = "Metro"
                color = "orange"
            elif any(x in str(row).lower() for x in ['metrobus', 'metrobús']):
                tipo = "Metrobús"
                color = "red"
            elif any(x in str(row).lower() for x in ['trolebus', 'trolebús', 'ste']):
                tipo = "Trolebús"
                color = "blue"
            
            point = row.get('geometry').centroid
            results.append({
                'name': f"{tipo} {name}", 
                'lat': point.y, 
                'lon': point.x,
                'tipo': tipo,
                'color': color
            })
        return results
    except Exception:
        return []
