import osmnx as ox
import networkx as nx
import folium

# 1. CONFIGURACIÓN
LUGAR = "Colonia Roma Norte, Ciudad de México, Mexico"
print(f"[1/6] Configurando Escenario: EL DESVÍO FORZOSO...")

ox.settings.use_cache = False 
ox.settings.useful_tags_way = ['name', 'highway', 'lit', 'surface']
G = ox.graph_from_place(LUGAR, network_type="walk")

# 2. FÓRMULA SANDOVAL (Estrategia: Lista Blanca Estricta)
print(f"[2/6] Aplicando lógica de ingeniería...")

for u, v, k, data in G.edges(keys=True, data=True):
    longitud = data.get('length', 0)
    nombre = str(data.get('name', 'Unknown')).lower()
    
    # COSTO BASE: Pánico (Todo es caro)
    costo_final = longitud * 10.0
    
    # LISTA BLANCA (Calles donde permitimos caminar)
    # Colima es nuestra salvación paralela
    nombres_seguros = ["colima", "tabasco", "guadalajara"]
    
    if any(vip in nombre for vip in nombres_seguros):
        costo_final = longitud * 1.0 # Costo real (barato)
    
    data['costo_sandoval'] = costo_final

# 3. PUNTOS TRAMPA (AMBOS SOBRE LA AVENIDA PROHIBIDA)
# Esto obliga a la ruta verde a "salirse" y luego "regresar".
# Inicio: Álvaro Obregón esq. Orizaba
origen_lat, origen_lon = 19.4188, -99.1609 
# Fin: Álvaro Obregón esq. Frontera (4 cuadras adelante)
destino_lat, destino_lon = 19.4208, -99.1566 

print(f"[3/6] Localizando nodos sobre Álvaro Obregón...")
nodo_origen = ox.nearest_nodes(G, origen_lon, origen_lat)
nodo_destino = ox.nearest_nodes(G, destino_lon, destino_lat)

# 4. CÁLCULO
print(f"[4/6] Calculando rutas...")

# Ruta Roja (Se irá recto por Obregón)
ruta_roja = nx.shortest_path(G, nodo_origen, nodo_destino, weight='length')
dist_roja = nx.shortest_path_length(G, nodo_origen, nodo_destino, weight='length')

# Ruta Verde (Tendría que subir a Colima y luego bajar)
ruta_verde = nx.shortest_path(G, nodo_origen, nodo_destino, weight='costo_sandoval')
dist_verde = nx.shortest_path_length(G, nodo_origen, nodo_destino, weight='length')

# 5. CHISMOSO (Verificar nombres)
print(f"--- FORENSE ---")
# Vemos las calles de la ruta verde
nombres = [G.get_edge_data(ruta_verde[i], ruta_verde[i+1])[0].get('name', 'X') for i in range(5)]
print(f"Ruta Verde empieza por: {nombres}")

# 6. RESULTADOS
print(f"--- SCORE FINAL ---")
print(f"Ruta Roja (Recta): {int(dist_roja)} metros.")
print(f"Ruta Verde (Desvío): {int(dist_verde)} metros.")
diferencia = int(dist_verde - dist_roja)
print(f"¡DIFERENCIA!: {diferencia} metros (Metros caminados extra por seguridad).")

# 7. MAPA
print(f"[5/6] Generando mapa...")
m = folium.Map(location=[origen_lat, origen_lon], zoom_start=16)

def pintar(ruta, color, peso):
    coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in ruta]
    folium.PolyLine(coords, color=color, weight=peso, opacity=0.8).add_to(m)

pintar(ruta_roja, "red", 4)
pintar(ruta_verde, "green", 5)

folium.Marker([origen_lat, origen_lon], popup="Inicio", icon=folium.Icon(color="black")).add_to(m)
folium.Marker([destino_lat, destino_lon], popup="Fin", icon=folium.Icon(color="black")).add_to(m)

m.save("mapa_desvio_final.html")
print(f"¡HECHO! Abre 'mapa_desvio_final.html'")