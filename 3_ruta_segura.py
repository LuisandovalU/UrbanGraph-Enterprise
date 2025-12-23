import osmnx as ox
import networkx as nx
import folium

# 1. CARGAR EL MAPA
LUGAR = "Benito Juárez, Ciudad de México, Mexico"
print(f"[1/5] Cargando el grafo de: {LUGAR}...")
G = ox.graph_from_place(LUGAR, network_type="walk")

# 2. HACKEANDO EL GRAFO (LA CLASE DE HOY) 🎓
print(f"[2/5] Aplicando penalizaciones a avenidas peligrosas...")

# Iteramos sobre todas las calles (aristas) del mapa
# u = nodo inicio, v = nodo fin, data = información de la calle
for u, v, data in G.edges(data=True):
    
    # Obtenemos el tipo de calle (highway)
    tipo_calle = data.get('highway', 'unknown')
    longitud = data.get('length', 0)
    
    # A veces 'tipo_calle' es una lista (ej. ['tertiary', 'residential'])
    # Lo convertimos a string para facilitar la comparación
    if isinstance(tipo_calle, list):
        tipo_calle = tipo_calle[0]
    
    # --- LÓGICA DE PASTOREO ---
    # Si es una avenida grande (primary) o tronco (trunk), es peligrosa/ruidosa
    if tipo_calle in ['primary', 'trunk', 'primary_link', 'secondary']:
        penalizacion = 10  # ¡Cuesta 10 veces más pasar por aquí!
    else:
        penalizacion = 1   # Calle normal, costo estándar
        
    # Creamos el nuevo atributo 'costo_pastoreo'
    # Costo = Metros Reales * Penalización
    data['costo_pastoreo'] = longitud * penalizacion

# 3. DEFINIR PUNTOS (Mismos de antes)
origen_lat, origen_lon = 19.3695, -99.1573 # Parque Venados
destino_lat, destino_lon = 19.3936, -99.1724 # WTC

nodo_origen = ox.nearest_nodes(G, origen_lon, origen_lat)
nodo_destino = ox.nearest_nodes(G, destino_lon, destino_lat)

# 4. CALCULAR LAS DOS RUTAS
print(f"[3/5] Calculando Ruta RÁPIDA (Dijkstra normal)...")
ruta_rapida = nx.shortest_path(G, nodo_origen, nodo_destino, weight='length')

print(f"[4/5] Calculando Ruta TRANQUILA (Dijkstra modificado)...")
# Nota que aquí usamos weight='costo_pastoreo' en lugar de 'length'
ruta_tranquila = nx.shortest_path(G, nodo_origen, nodo_destino, weight='costo_pastoreo')

# 5. VISUALIZACIÓN COMPARATIVA
print(f"[5/5] Generando mapa comparativo...")

# Función auxiliar para dibujar rutas (para no repetir código)
def dibujar_ruta(mapa, grafo, ruta, color, grosor):
    coords = [(grafo.nodes[n]['y'], grafo.nodes[n]['x']) for n in ruta]
    folium.PolyLine(coords, color=color, weight=grosor, opacity=0.8).add_to(mapa)

# Mapa base
m = folium.Map(location=[origen_lat, origen_lon], zoom_start=14)

# Dibujamos Ruta Rápida (ROJO)
dibujar_ruta(m, G, ruta_rapida, color="red", grosor=4)

# Dibujamos Ruta Tranquila (VERDE)
dibujar_ruta(m, G, ruta_tranquila, color="green", grosor=4)

# Marcadores
folium.Marker([origen_lat, origen_lon], popup="Inicio", icon=folium.Icon(color="black")).add_to(m)
folium.Marker([destino_lat, destino_lon], popup="Destino", icon=folium.Icon(color="black")).add_to(m)

# Leyenda (truco simple con HTML)
leyenda_html = '''
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 90px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; opacity:0.9; padding: 10px;">
     <b>Leyenda:</b><br>
     <span style="color:red">__</span> Más Rápida<br>
     <span style="color:green">__</span> Más Tranquila
     </div>
     '''
m.get_root().html.add_child(folium.Element(leyenda_html))

m.save("comparacion_rutas.html")
print("¡HECHO! Abre 'comparacion_rutas.html'.")
print("La ROJA es la que te daría Google Maps.")
print("La VERDE es la que te da tu algoritmo 'Shepherd'.")