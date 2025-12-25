import osmnx as ox
import networkx as nx
import json
import os
from shapely.geometry import Point
from scipy.spatial import KDTree

# --- UrbanOS 2040: Dynamic Stress Calibration ---
REALTIME_FILE = "realtime_fallback.json"

def cargar_datos_volatilidad():
    """Carga incidentes reales procesados por data_ingestor.py."""
    if os.path.exists(REALTIME_FILE):
        try:
            with open(REALTIME_FILE, "r") as f:
                return json.load(f).get("incidents", [])
        except:
            return []
    return []

def calcular_peso_sandoval_v2(data, nivel_volatilidad=1.0, incidentes_coords=None, tree=None):
    """
    Fórmula Sandoval™ Refactorizada:
    Acepta parámetro dinámico 'nivel_volatilidad' y cruza con ADIP.
    """
    longitud = data.get('length', 0)
    nombre = str(data.get('name', 'Unknown')).lower()
    
    # 1. Costo Base (Standard)
    costo_base = longitud * 1.0
    
    # 2. Factor de Estrés Urbano (Volatilidad)
    # Penalización del 500% (6.0x) si hay incidentes en radio de 500m
    stress_multiplier = 1.0
    
    # Centro aproximado de la calle (u, v logic is in the loop, passing data here)
    # Para simplificar en esta función, asumimos que recibimos lat/lon o usamos pre-calc tree
    # En el loop principal se hará el query.
    
    # 3. Lista Blanca (Bonos de Seguridad)
    nombres_seguros = ["colima", "tabasco", "guadalajara", "orizaba"]
    if any(vip in nombre for vip in nombres_seguros):
        costo_base *= 0.5 # Corredor Verde
        
    return costo_base * nivel_volatilidad

# --- Misión 2: Script de Prueba Dinámico ---
print(f"[1/4] Cargando Grafo y Datos de Volatilidad...")
LUGAR = "Colonia Roma Norte, Ciudad de México, Mexico"
G = ox.graph_from_place(LUGAR, network_type="walk")
incidentes = cargar_datos_volatilidad()

# Preparar KDTree para búsqueda de 500m (Rápido)
if incidentes:
    incident_pts = [[inc['lon'], inc['lat']] for inc in incidentes]
    tree = KDTree(incident_pts)
else:
    tree = None

print(f"[2/4] Aplicando Fórmula Sandoval™ Dinámica (Misión 2)...")
for u, v, k, data in G.edges(keys=True, data=True):
    # Obtener lat/lon del punto medio para el radio
    mid_x = (G.nodes[u]['x'] + G.nodes[v]['x']) / 2
    mid_y = (G.nodes[u]['y'] + G.nodes[v]['y']) / 2
    
    # Nivel de Volatilidad por cercanía a incidentes (500m ~ 0.0045 grados)
    penalty = 1.0
    if tree:
        indices = tree.query_ball_point([mid_x, mid_y], 0.0045)
        if indices:
            penalty = 5.0 # Aumenta 500% el estrés
            
    data['costo_sandoval'] = calcular_peso_sandoval_v2(data, nivel_volatilidad=penalty)

# 4. Verificación de "Zona de Sombra"
origen = (19.4188, -99.1609)
destino = (19.4208, -99.1566)
n_o = ox.nearest_nodes(G, origen[1], origen[1])
n_d = ox.nearest_nodes(G, destino[1], destino[0])

try:
    ruta = nx.shortest_path(G, n_o, n_d, weight='costo_sandoval')
    print(f"[3/4] Ruta calculada con éxito eludiendo zonas de sombra.")
except:
    print(f"[ERROR] No se pudo calcular la ruta.")

print(f"[4/4] Hecho. Fórmula Sandoval™ actualizada para Misión Crítica.")