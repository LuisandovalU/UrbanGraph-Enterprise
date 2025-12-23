import osmnx as ox
import networkx as nx
import requests
import random
import time
import logging
import json
import os
import numpy as np
from scipy.spatial import KDTree
from typing import Dict, List, Optional, Tuple

# --- UrbanOS 2040: Configuración de Logs ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("urbanos_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UrbanOS")

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
    """Descarga y prepara el grafo base de la Ciudad de México.

    Configura los tags útiles de OSMnx y descarga la red peatonal para la ubicación
    definida en el RISK_PROFILE.

    Returns:
        nx.MultiDiGraph: El grafo de la red peatonal listo para procesamiento.

    Raises:
        Exception: Si ocurre un error durante la descarga o procesamiento del grafo.
    """
    ox.settings.useful_tags_way = ['name', 'highway', 'length']
    return ox.graph_from_place(RISK_PROFILE["LOCATION"], network_type="walk")

# --- UrbanOS 2040: Inteligencia de Tiempo Real ---

# Guardián de Resiliencia: Circuit Breaker Configuration
FETCH_TIMEOUT = 3.0  # Segundos (Senior Backend Standard)
BACKUP_FILE = "backup_data.json"

def fetch_realtime_data() -> Dict:
    """Orquesta la ingesta de datos con patrón Circuit Breaker y Respaldo Local.

    Pilar 1: Consulta APIs externas (Ecobici y C5) con un límite de 3 segundos.
    Si ocurre un fallo o timeout, carga automáticamente 'backup_data.json'
    para mantener la continuidad del servicio.

    Returns:
        Dict: Estructura de datos tácticos que incluye:
            - ecobici (Dict): Disponibilidad por estación.
            - incidents (List): Alertas geolocalizadas.
            - integrity (str): Estatus de salud del sistema.
            - metrics (Dict): Latencia, fidelidad y marca de tiempo.
    """
    data = {
        "ecobici": {}, 
        "incidents": [], 
        "integrity": "Optimal",
        "metrics": {
            "latency_ms": 0, 
            "fidelity": 100,
            "last_sync": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    success_count = 0
    total_sources = 2
    start_time = time.time()

    try:
        # 1. Ecobici Availability (Timeout de 3s)
        url_eco = "https://gbfs.mex.lyftbikes.com/gbfs/es/station_status.json"
        try:
            res = requests.get(url_eco, timeout=FETCH_TIMEOUT)
            if res.status_code == 200:
                stations = res.json()["data"]["stations"]
                data["ecobici"] = {s["station_id"]: s["num_bikes_available"] for s in stations}
                valid_reports = sum(1 for s in stations if s.get("last_reported", 0) > 0)
                data["metrics"]["fidelity"] = int((valid_reports / len(stations) * 100)) if stations else 100
                success_count += 1
                logger.info("Sync Audit: Ecobici data consumed successfully.")
            else:
                logger.error(f"Sync Audit: Ecobici API status {res.status_code}")
        except requests.Timeout:
            logger.warning("Sync Audit: Ecobici API Timeout (3s). Circuit Breaker engaged.")
        except Exception as e:
            logger.error(f"Sync Audit: Ecobici Error: {e}")

        # 2. CDMX Real-time Incidents (Timeout de 3s)
        resource_id = "59d5ede6-7af8-4384-a114-f84ff1b26fe1"
        url_c5 = f"https://datos.cdmx.gob.mx/api/3/action/datastore_search?resource_id={resource_id}&limit=50&q=BENITO+JUAREZ"
        try:
            res = requests.get(url_c5, timeout=FETCH_TIMEOUT)
            if res.status_code == 200:
                records = res.json()["result"]["records"]
                for rec in records:
                    if rec.get("latitud") and rec.get("longitud"):
                        data["incidents"].append({
                            "tipo": rec.get("incidente_c4", "Incidente Vial"),
                            "lat": float(rec["latitud"]),
                            "lon": float(rec["longitud"]),
                            "impacto": 3.0,
                            "color": "red"
                        })
                success_count += 1
                logger.info("Sync Audit: C5 Incidents ingested successfully.")
            else:
                logger.error(f"Sync Audit: C5 API status {res.status_code}")
        except requests.Timeout:
            logger.warning("Sync Audit: C5 API Timeout (3s). Circuit Breaker engaged.")
        except Exception as e:
            logger.error(f"Sync Audit: C5 Error: {e}")

        # --- Análisis de Telemetría ---
        data["metrics"]["latency_ms"] = int((time.time() - start_time) * 1000)
        
        if success_count == total_sources:
            data["integrity"] = "Optimal"
            with open(BACKUP_FILE, "w") as f:
                json.dump(data, f)
        elif success_count > 0:
            data["integrity"] = "Degraded"
        else:
            raise Exception("All data sources are offline.")

    except Exception as e:
        logger.critical(f"Sync Audit: Global Failure: {e}. Orchestrating data fallback.")
        data["integrity"] = "Critical (Resiliencia Activa)"
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, "r") as f:
                backup = json.load(f)
                data.update({
                    "ecobici": backup.get("ecobici", {}),
                    "incidents": backup.get("incidents", []),
                    "metrics": backup.get("metrics", {"latency_ms": -1, "fidelity": 0, "last_sync": "Fallback Data"})
                })
        else:
            logger.warning("Resilience Audit: No backup_data.json found. System running empty.")

    return data

def obtener_disponibilidad_ecobici() -> Dict[str, int]:
    """Provee acceso rápido a la disponibilidad de Ecobici.

    Returns:
        Dict[str, int]: Diccionario con ID de estación y número de bicicletas disponibles.
    """
    return fetch_realtime_data()["ecobici"]

def generar_incidentes_sinteticos(G) -> List[Dict]:
    """Genera incidentes hipotéticos para demostración de seguridad proactiva.

    Args:
        G (nx.MultiDiGraph): El grafo urbano donde se inyectarán los incidentes.

    Returns:
        List[Dict]: Lista de incidentes simulados con tipo, impacto y coordenadas.
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

def build_graph_spatial_index(G) -> Tuple[KDTree, List]:
    """Construye un índice espacial para el grafo urbano.

    Optimización O(log N): Permite mapear puntos geográficos a los nodos
    del grafo con una velocidad de grado industrial.

    Args:
        G (nx.MultiDiGraph): El grafo urbano.

    Returns:
        Tuple[KDTree, List]: El árbol de búsqueda y la lista ordenada de IDs de nodos.
    """
    nodes = []
    coords = []
    for node_id, data in G.nodes(data=True):
        nodes.append(node_id)
        coords.append((data['x'], data['y']))
    return KDTree(coords), nodes

def aplicar_formula_sandoval(G, weather_impact=1.0, hurry_factor=50.0, incidentes: List[Dict] = None, realtime_data: Dict = None):
    """Aplica la Función de Costo Generalizado Sandoval 2.4 (Enterprise).

    Calcula la impedancia de cada arista balanceando longitud, riesgo y eventos.
    Utiliza KDTree para una inserción de incidentes de alto rendimiento.

    Args:
        G (nx.MultiDiGraph): El grafo urbano a procesar.
        weather_impact (float): Factor por condiciones climáticas.
        hurry_factor (float): Estilo de conducción/prisa (0-100).
        incidentes (List[Dict]): Incidentes tácticos del C5.
        realtime_data (Dict): Feed dinámico de APIs externas.

    Returns:
        nx.MultiDiGraph: El grafo con pesos actualizados.
    """
    h_ratio = hurry_factor / 100.0
    s_ratio = 1.0 - h_ratio
    
    # Consolidación de incidentes con alto rendimiento
    all_incidents = (incidentes or [])
    if realtime_data and "incidents" in realtime_data:
        all_incidents.extend(realtime_data["incidents"])
    
    # Mapeo espacial ultra-rápido usando KDTree
    tree, node_ids = build_graph_spatial_index(G)
    incidents_map = {}
    
    if all_incidents:
        for inc in all_incidents:
            if "node" in inc:
                incidents_map[inc["node"]] = inc["impacto"]
            else:
                # Búsqueda O(log N) en lugar de O(N)
                _, idx = tree.query((inc["lon"], inc["lat"]))
                target_node = node_ids[idx]
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
    """Calcula la trayectoria óptima entre dos puntos geográficos.

    Args:
        G (nx.MultiDiGraph): El grafo con pesos ya calculados.
        coords_orig (Tuple[float, float]): Latitud y longitud de origen.
        coords_dest (Tuple[float, float]): Latitud y longitud de destino.
        criterio (str, optional): Atributo de arista a optimizar. Defaults to 'final_impedance'.

    Returns:
        Tuple: (lista_de_nodos, id_nodo_origen, id_nodo_destino).
               lista_de_nodos será None si no hay trayecto posible.
    """
    n_orig = ox.nearest_nodes(G, coords_orig[1], coords_orig[0])
    n_dest = ox.nearest_nodes(G, coords_dest[1], coords_dest[0])
    
    try:
        ruta = nx.shortest_path(G, n_orig, n_dest, weight=criterio)
        return ruta, n_orig, n_dest
    except nx.NetworkXNoPath:
        return None, n_orig, n_dest

def obtener_analisis_multi_ruta(G, coords_orig, coords_dest, hurry_factor=50.0, weather_impact=1.0, incidentes: List[Dict] = None, realtime_data: Dict = None):
    """Realiza un análisis comparativo de trayectorias (Escudo vs Relámpago vs Directa).

    Args:
        G (nx.MultiDiGraph): El grafo base.
        coords_orig (Tuple[float, float]): Coordenadas de inicio.
        coords_dest (Tuple[float, float]): Coordenadas de fin.
        hurry_factor (float): Nivel de audacia/prisa.
        weather_impact (float): Impacto ambiental.
        incidentes (List[Dict], optional): Lista de alertas.
        realtime_data (Dict, optional): Datos de APIs en vivo.

    Returns:
        Dict: Analítica de rutas incluyendo nodos de trayectoria y puntos críticos.
    """
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
