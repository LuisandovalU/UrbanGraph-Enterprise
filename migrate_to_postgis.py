import osmnx as ox
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import argparse
import time

load_dotenv()

# --- Configuración de Base de Datos ---
DB_URL = os.getenv("DATABASE_URL", "postgresql://sandoval:enterprise_pro_2040@localhost:5432/urbangraph")

def setup_spatial_indices(engine):
    """Demostración de Big Data: Creación de índices espaciales GIST."""
    print("[DP] Configurando Índices Espaciales GIST para alto rendimiento...")
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_nodes_geometry ON nodes USING GIST (geometry);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_edges_geometry ON edges USING GIST (geometry);"))
        conn.commit()

def migrate_graph_to_postgis(demo_mode=False):
    """Migra el grafo vial actual de GraphML a PostGIS con lógica de control."""
    print(f"[1/3] Cargando grafo (Modo Demo: {demo_mode})...")
    # Misión 10: Escalamiento a Iztapalapa
    graph_path = "iztapalapa_seguro.graphml"
    
    if not os.path.exists(graph_path):
        print("[Misión 10] Descargando Red Vial Completa de Iztapalapa (High Load Simulation)...")
        # Iztapalapa es una de las alcaldías más densas de CDMX, ideal para prueba de carga.
        G = ox.graph_from_place("Iztapalapa, Ciudad de México, Mexico", network_type="walk")
        ox.save_graphml(G, graph_path)
    else:
        G = ox.load_graphml(graph_path)

    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

    if demo_mode:
        print("[DEMO] Limitando carga para demostración (10% de la red)...")
        nodes_gdf = nodes_gdf.sample(frac=0.1)
        edges_gdf = edges_gdf[edges_gdf.index.get_level_values(0).isin(nodes_gdf.index)]

    print(f"[2/3] Insertando en PostGIS: {DB_URL}")
    try:
        engine = create_engine(DB_URL)
        start_time = time.time()
        
        # Inserción con GeoPandas (Soporta Geometría Nativa PostGIS)
        nodes_gdf.to_postgis("nodes", engine, if_exists="replace", index=True)
        edges_gdf.to_postgis("edges", engine, if_exists="replace", index=True)
        
        duration = time.time() - start_time
        print(f"MIGRACIÓN COMPLETADA en {duration:.2f}s.")
        
        # Misión 7: Demostración de Índices
        setup_spatial_indices(engine)
        print("MIGRACIÓN EXITOSA. Grafo de Iztapalapa disponible y optimizado.")
    except Exception as e:
        print(f"FALLO EN MIGRACIÓN: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UrbanGraph PostGIS Migrator")
    parser.add_argument("--demo", action="store_true", help="Habilitar modo demostración Big Data")
    args = parser.parse_args()
    
    migrate_graph_to_postgis(demo_mode=args.demo)
