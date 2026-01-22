#!/usr/bin/env python3
"""Example usage of UrbanGraph Engine."""
from urban_graph_engine.core import engine

# Load graph
print("Loading graph...")
G = engine.cargar_grafo_seguro()
print(f"Graph loaded with {len(G.nodes)} nodes.")

# Example route
orig = (19.3948, -99.1736)  # WTC
dest = (19.4206, -99.1626)  # Another point

print("Calculating route...")
ruta, n_orig, n_dest = engine.calcular_ruta_optima(G, orig, dest)
if ruta:
    print(f"Route found: {len(ruta)} nodes")
    # Evaluate integrity
    integrity = engine.evaluar_integridad_ruta([(G.nodes[n]['y'], G.nodes[n]['x']) for n in ruta])
    print(f"Integrity score: {integrity['integrity_score']}")
else:
    print("No route found.")