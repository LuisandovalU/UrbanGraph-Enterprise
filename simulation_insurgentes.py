import engine
import osmnx as ox
import networkx as nx
import json
import os
import time

def simulation_insurgentes():
    print("🚦 INICIANDO SIMULACIÓN DE CAOS: Insurgentes & Félix Cuevas")
    
    # 1. ESCENARIO A: Línea Base (San Ángel -> Reforma)
    # San Ángel (Vía San Ángel) approx
    p_orig = (19.3475, -99.1915) 
    # Reforma (Angel de la Independencia) approx
    p_dest = (19.4270, -99.1677)
    
    print(f"\n[Fase A] Calculando ruta base (Sin Incidentes)...")
    G = engine.cargar_grafo_seguro()
    # Aseguramos que no haya incidentes previos
    realtime_empty = {"incidents": [], "status": "Clean"}
    
    # Usamos Relámpago (Balanced) con h_factor 50
    analysis_a = engine.obtener_analisis_multi_ruta(G, p_orig, p_dest, hurry_factor=50.0, realtime_data=realtime_empty)
    ruta_a = analysis_a['relampago']
    score_a = analysis_a['integrity_score']
    
    print(f"✅ Ruta A calculada satisfactoriamente.")
    print(f"📊 Integrity Score (Base): {score_a}")
    
    # Validar si pasa por Insurgentes (Simple check by edge names)
    passes_insurgentes = False
    for u, v, k, data in G.edges(keys=True, data=True):
        if u in ruta_a and v in ruta_a:
            if "insurgentes" in str(data.get('name', '')).lower():
                passes_insurgentes = True
                break
    
    if passes_insurgentes:
        print("📍 Confirmado: La ruta base utiliza Avenida Insurgentes Sur.")
    else:
        print("⚠️ Advertencia: La ruta base no detectó Insurgentes. Verificando coordenadas...")

    # 2. INYECCIÓN DE CAOS (Block at Felix Cuevas)
    # Félix Cuevas e Insurgentes
    block_lat, block_lon = 19.3742, -99.1776
    print(f"\n[Fase B] Inyectando Bloqueo Crítico en Félix Cuevas & Insurgentes...")
    incidentes_caos = [{
        "tipo": "BLOQUEO_C5",
        "lat": block_lat,
        "lon": block_lon,
        "impacto": 10.0
    }]
    realtime_caos = {"incidents": incidentes_caos, "status": "Bloqueo Activo"}

    # 3. ESCENARIO B: Reacción (Misma ruta con Caos)
    print(f"[Fase C] Calculando nueva ruta con incidente activo...")
    analysis_b = engine.obtener_analisis_multi_ruta(G, p_orig, p_dest, hurry_factor=50.0, realtime_data=realtime_caos)
    ruta_b = analysis_b['relampago']
    score_b = analysis_b['integrity_score']
    
    print(f"📊 Integrity Score (Post-Caos): {score_b}")
    
    # 4. VALIDACIÓN DE DESVÍO
    # El desvío debe evitar el radio de 500m del bloqueo
    avoids_block = True
    for node in ruta_b:
        node_data = G.nodes[node]
        dist = ((node_data['y'] - block_lat)**2 + (node_data['x'] - block_lon)**2)**0.5
        if dist < 0.0045: # 500m logic from engine.py
            avoids_block = False
            break
            
    if avoids_block:
        print("🚀 ÉXITO: La nueva ruta evita la zona de sombra del bloqueo.")
    else:
        print("❌ FALLO: La ruta sigue pasando por la zona del incidente.")

    # Verificar si cambió la ruta
    if ruta_a != ruta_b:
        print("🛤️  Confirmado: Redirección dinámica detectada.")
    else:
        print("🛑  Advertencia: Las rutas son idénticas a pesar del bloqueo.")

if __name__ == "__main__":
    simulation_insurgentes()
