import osmnx as ox
import networkx as nx
import requests
import random
import time
from typing import Dict, List, Optional

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

# --- UrbanOS 2040: Inteligencia de Tiempo Real ---

def fetch_realtime_data() -> Dict:
    """
    Pilar 1: Orquestación en Tiempo Real.
    Consulta Ecobici (GBFS) e Incidentes Viales (CDMX Open Data).
    """
    data = {"ecobici": {}, "incidents": []}
    
    # 1. Ecobici Availability
    url_eco = "https://gbfs.mex.lyftbikes.com/gbfs/es/station_status.json"
    try:
        res = requests.get(url_eco, timeout=5)
        if res.status_code == 200:
            data["ecobici"] = {s["station_id"]: s["num_bikes_available"] for s in res.json()["data"]["stations"]}
    except Exception as e: print(f"Ecobici Error: {e}")
    
    # 2. CDMX Real-time Incidents (C5)
    # Resource: Incidentes Viales (2022-2024)
    resource_id = "59d5ede6-7af8-4384-a114-f84ff1b26fe1"
    url_c5 = f"https://datos.cdmx.gob.mx/api/3/action/datastore_search?resource_id={resource_id}&limit=50&q=BENITO+JUAREZ"
    try:
        res = requests.get(url_c5, timeout=5)
        if res.status_code == 200:
            records = res.json()["result"]["records"]
            for rec in records:
                if rec.get("latitud") and rec.get("longitud"):
                    data["incidents"].append({
                        "tipo": rec.get("incidente_c4", "Incidente Vial"),
                        "lat": float(rec["latitud"]),
                        "lon": float(rec["longitud"]),
                        "impacto": 3.0, # Impacto base para incidentes reales
                        "color": "red"
                    })
    except Exception as e: print(f"C5 API Error: {e}")
    
    return data

def obtener_disponibilidad_ecobici() -> Dict[str, int]:
    """Shorthand para compatibilidad con UI."""
    return fetch_realtime_data()["ecobici"]

def generar_incidentes_sinteticos(G) -> List[Dict]:
    """
    Pilar 7: Seguridad Proactiva. 
    Simula incidentes (C5/Luminarias) en nodos aleatorios del grafo para demostración.
    """
    incident_types = [
        {"tipo": "C5: Incidente Reportado", "impacto": 5.0, "icon": "exclamation-triangle", "color": "orange"},
        {"tipo": "Falla de Luminaria", "impacto": 1.5, "icon": "lightbulb", "color": "yellow"},
        {"tipo": "Obra en Vía", "impacto": 3.0, "icon": "hard-hat", "color": "brown"}
    ]
    nodos = list(G.nodes)
    num_incidentes = random.randint(3, 8)
    incidentes = []
    
    for _ in range(num_incidentes):
        node_id = random.choice(nodos)
        tipo = random.choice(incident_types)
        node_data = G.nodes[node_id]
        incidentes.append({
            "node": node_id,
            "lat": node_data['y'],
            "lon": node_data['x'],
            **tipo
        })
    return incidentes

def aplicar_formula_sandoval(G, weather_impact=1.0, hurry_factor=50.0, incidentes: List[Dict] = None, realtime_data: Dict = None):
    """
    Aplica la Función de Costo Generalizado Sandoval 2.4 (Enterprise).
    Pilar 1: Integración de Datos Reales.
    """
    h_ratio = hurry_factor / 100.0
    s_ratio = 1.0 - h_ratio
    
    # Consolidar incidentes (Sintéticos + Reales)
    all_incidents = (incidentes or [])
    if realtime_data and "incidents" in realtime_data:
        all_incidents.extend(realtime_data["incidents"])
    
    # Mapeo espacial de incidentes a nodos
    incidents_map = {}
    if all_incidents:
        for inc in all_incidents:
            if "node" in inc:
                incidents_map[inc["node"]] = inc["impacto"]
            else:
                # Si no tiene nodo, buscar el más cercano (aproximado para performance)
                target_node = ox.nearest_nodes(G, inc["lon"], inc["lat"])
                incidents_map[target_node] = max(incidents_map.get(target_node, 0), inc["impacto"])

    # Mapa de Ecobici (Pilar 1: Estaciones vacías anulan bono)
    # Nota: Aquí asumimos que la UI maneja la relación Node/StationID o usamos proximidad
    ecobici_stock = realtime_data.get("ecobici", {}) if realtime_data else {}

    for u, v, k, data in G.edges(keys=True, data=True):
        segment_length = data.get('length', 10.0)
        street_name = str(data.get('name', '')).lower()
        
        highway = data.get('highway', 'unclassified')
        if isinstance(highway, list): highway = highway[0]
        highway_type = str(highway).lower()
        
        # 1. RIESGO BASE
        risk_multiplier = RISK_PROFILE["WEIGHTS"]["STANDARD"]
        if any(safe_key in street_name for safe_key in RISK_PROFILE["KEYWORDS"]["SAFE"]):
            risk_multiplier = RISK_PROFILE["WEIGHTS"]["SAFE"]
        if any(danger_key in street_name for danger_key in RISK_PROFILE["KEYWORDS"]["DANGER"]):
            risk_multiplier = RISK_PROFILE["WEIGHTS"]["DANGER"]
            
        # 2. BONOS DE INFRAESTRUCTURA (Pilar 4)
        is_avenue = any(av in street_name for av in ['insurgentes', 'eje central', 'universidad', 'cuauhtemoc', 'division del norte'])
        is_fast = any(av in highway_type for av in ['primary', 'secondary', 'tertiary'])
        is_micro = any(path in highway_type for path in ['footway', 'pedestrian', 'path', 'cycleway', 'living_street'])
        
        avenue_bonus = 0.6 if (is_avenue or is_fast) else 1.0
        
        # Lógica Ecobici: Si el nodo u o v es una estación vacía, no hay micro_bonus total?
        # En esta versión simplificada, mantenemos el micro_bonus base pero lo reducimos si hay incidentes
        micro_bonus = 0.4 if is_micro else 1.0
        
        # 3. IMPACTO DINÁMICO (Incidentes Reales + Sintéticos)
        incident_impact = 1.0
        if u in incidents_map or v in incidents_map:
            incident_impact = max(incidents_map.get(u, 1.0), incidents_map.get(v, 1.0))

        # 4. FORMULACIÓN SANDOVAL 2.4
        dynamic_s_ratio = s_ratio if h_ratio <= 0.7 else s_ratio * 0.5
        
        riesgo_base = (risk_multiplier * weather_impact * incident_impact)
        riesgo_ajustado = riesgo_base * dynamic_s_ratio
        
        data['final_impedance'] = (segment_length * avenue_bonus * micro_bonus * h_ratio) + \
                                 (segment_length * riesgo_ajustado * 5.0 * dynamic_s_ratio)
        
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

def obtener_analisis_multi_ruta(G, coords_orig, coords_dest, hurry_factor=50.0, weather_impact=1.0, incidentes: List[Dict] = None, realtime_data: Dict = None):
    """Calcula simultáneamente las tres rutas: Escudo, Relámpago y Directa."""
    # 1. Ruta Directa (Rapidez Pura)
    r_directa, n_orig, n_dest = calcular_ruta_optima(G, coords_orig, coords_dest, criterio='length')
    
    # 2. Ruta Escudo (Seguridad Total - prisa 0)
    # En Escudo, los incidentes pesan el doble para forzar desvíos
    incidentes_escudo = []
    if incidentes:
        for inc in incidentes:
            new_inc = inc.copy()
            new_inc["impacto"] *= 2.0
            incidentes_escudo.append(new_inc)

    G_escudo = aplicar_formula_sandoval(G.copy(), weather_impact=weather_impact, hurry_factor=0, incidentes=incidentes_escudo, realtime_data=realtime_data)
    r_escudo, _, _ = calcular_ruta_optima(G_escudo, coords_orig, coords_dest)
    
    # 3. Ruta Relámpago (Balanceada - según slider)
    G_relampago = aplicar_formula_sandoval(G.copy(), weather_impact=weather_impact, hurry_factor=hurry_factor, incidentes=incidentes, realtime_data=realtime_data)
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
