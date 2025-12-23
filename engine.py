import osmnx as ox
import networkx as nx

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
    "LOCATION": "Colonia Roma Norte, Ciudad de México, Mexico"
}

def cargar_grafo_seguro():
    """Descarga y prepara el grafo base."""
    ox.settings.use_cache = True
    ox.settings.useful_tags_way = ['name', 'highway', 'length']
    return ox.graph_from_place(RISK_PROFILE["LOCATION"], network_type="walk")

def aplicar_formula_sandoval(G, weather_impact=1.0):
    """
    Aplica la Función de Costo Generalizado.
    Sincronizado con el nuevo atributo: final_impedance.
    weather_impact: Multiplicador de riesgo (ej. 1.2 si llueve).
    """
    for u, v, k, data in G.edges(keys=True, data=True):
        segment_length = data.get('length', 10.0)
        street_name = str(data.get('name', '')).lower()
        
        # Lógica de peso por defecto
        risk_factor = RISK_PROFILE["WEIGHTS"]["STANDARD"]
        
        # Aplicación de capas de riesgo (Estático)
        if any(safe_key in street_name for safe_key in RISK_PROFILE["KEYWORDS"]["SAFE"]):
            risk_factor = RISK_PROFILE["WEIGHTS"]["SAFE"]
            
        if any(danger_key in street_name for danger_key in RISK_PROFILE["KEYWORDS"]["DANGER"]):
            risk_factor = RISK_PROFILE["WEIGHTS"]["DANGER"]
            
        # El corazón de la API: el peso final afectado por clima/eventos
        data['final_impedance'] = segment_length * risk_factor * weather_impact
        
    return G

def calcular_ruta_optima(G, coords_orig, coords_dest, criterio='final_impedance'):
    """Calcula la ruta usando el motor de pesos Sandoval."""
    n_orig = ox.nearest_nodes(G, coords_orig[1], coords_orig[0])
    n_dest = ox.nearest_nodes(G, coords_dest[1], coords_dest[0])
    
    ruta = nx.shortest_path(G, n_orig, n_dest, weight=criterio)
    return ruta, n_orig, n_dest
