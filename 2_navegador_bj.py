import osmnx as ox
import networkx as nx
import folium

# 1. CONFIGURACIÓN
LUGAR = "Benito Juárez, Ciudad de México, Mexico"
print(f"[1/4] Cargando mapa de: {LUGAR}...")

# Descargamos el grafo
G = ox.graph_from_place(LUGAR, network_type="walk")

# 2. DEFINIR ORIGEN Y DESTINO
origen_lat, origen_lon = 19.3695, -99.1573 # Parque de los Venados
destino_lat, destino_lon = 19.3936, -99.1724 # WTC

print(f"[2/4] Buscando intersecciones...")
nodo_origen = ox.nearest_nodes(G, origen_lon, origen_lat)
nodo_destino = ox.nearest_nodes(G, destino_lon, destino_lat)

# 3. CALCULAR RUTA
print(f"[3/4] Calculando ruta óptima...")
ruta = nx.shortest_path(G, nodo_origen, nodo_destino, weight='length')

# 4. VISUALIZACIÓN MANUAL (La nueva forma Pro)
print(f"[4/4] Dibujando mapa...")

# Extraemos las coordenadas (Latitud, Longitud) de cada nodo de la ruta
route_coords = []
for node in ruta:
    # G.nodes[node] nos da los datos del punto. 'y' es latitud, 'x' es longitud.
    point = (G.nodes[node]['y'], G.nodes[node]['x'])
    route_coords.append(point)

# Creamos el mapa base centrado en el inicio
m = folium.Map(location=[origen_lat, origen_lon], zoom_start=14)

# Dibujamos la línea de la ruta
folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

# Agregamos marcadores
folium.Marker([origen_lat, origen_lon], popup="Inicio", icon=folium.Icon(color="green")).add_to(m)
folium.Marker([destino_lat, destino_lon], popup="Destino", icon=folium.Icon(color="red")).add_to(m)

# Guardamos
m.save("ruta_venados_wtc.html")
print(f"¡ÉXITO! Abre 'ruta_venados_wtc.html' en tu carpeta.")