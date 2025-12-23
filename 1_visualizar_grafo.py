import osmnx as ox
import matplotlib.pyplot as plt

# 1. CONFIGURACIÓN
# Definimos exactamente qué queremos descargar.
LUGAR = "Benito Juárez, Ciudad de México, Mexico"

print(f"--- INICIANDO SISTEMA ---")
print(f"Descargando datos viales para: {LUGAR}")
print("Esto puede tardar un poco dependiendo de tu internet...")

# 2. DESCARGA DEL GRAFO
# network_type="walk" significa que solo bajamos calles donde se puede caminar.
# simplify=True limpia el mapa para quitar nodos inútiles (curvas suaves).
G = ox.graph_from_place(LUGAR, network_type="walk", simplify=True)

print("¡Datos descargados correctamente!")

# 3. ESTADÍSTICAS BÁSICAS (Para tu documentación)
# Vamos a ver qué tan complejo es este mapa.
num_nodos = len(G.nodes)
num_calles = len(G.edges)
print(f"Estadísticas del Grafo:")
print(f"- Número de intersecciones (Nodos): {num_nodos}")
print(f"- Número de calles (Aristas): {num_calles}")

# 4. VISUALIZACIÓN RÁPIDA (Plot estático)
print("Generando imagen del grafo (esqueleto)...")
fig, ax = ox.plot_graph(G, node_size=0, edge_color="white", edge_linewidth=0.5, bgcolor="black")

print("Proceso terminado. Deberías ver una ventana con el mapa en negro.") 