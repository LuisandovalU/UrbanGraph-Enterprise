# import pytest (eliminado para ejecución directa)
import networkx as nx
# Importación dinámica desde el archivo de la app
import sys
from types import ModuleType

# Cargamos 5_app_web como un módulo para poder testear sus funciones
import importlib.util
spec = importlib.util.spec_from_file_location("app_web", "/Users/luisalbertosandovalramos/Desktop/UrbanGraph-Engine/5_app_web.py")
app_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_web)

calcular_pesos_dinamicos = app_web.calcular_pesos_dinamicos
RISK_PROFILE = app_web.RISK_PROFILE

def test_pesos_del_algoritmo():
    """
    Verifica que la Función de Costo aplique correctamente los pesos 
    del RISK_PROFILE basados en los nombres de las calles.
    """
    # 1. Setup: Crear un Grafo Simulado (Mock)
    G = nx.MultiDiGraph()
    
    # Agregar Arista A: Calle Segura (ej. Colima)
    G.add_edge(1, 2, key=0, length=100.0, name='Calle Colima')
    
    # Agregar Arista B: Zona de Peligro (ej. Insurgentes)
    G.add_edge(2, 3, key=0, length=100.0, name='Av Insurgentes Sur')
    
    # Agregar Arista C: Calle Estándar (Nombre X)
    G.add_edge(3, 4, key=0, length=100.0, name='Calle X')

    # 2. Ejecución: Correr la lógica
    G_procesado = calcular_pesos_dinamicos(G)

    # 3. Aserción: Verificar la Matemática
    
    # Caso Seguro: 100m * 1.0 = 100
    edge_safe = G_procesado[1][2][0]
    expected_safe = 100.0 * RISK_PROFILE["WEIGHTS"]["SAFE"]
    assert edge_safe['final_impedance'] == expected_safe, f"Fallo en peso Seguro. Se obtuvo {edge_safe['final_impedance']}"

    # Caso Peligro: 100m * 50.0 = 5000
    edge_danger = G_procesado[2][3][0]
    expected_danger = 100.0 * RISK_PROFILE["WEIGHTS"]["DANGER"]
    assert edge_danger['final_impedance'] == expected_danger, f"Fallo en peso Peligro. Se obtuvo {edge_danger['final_impedance']}"

    # Caso Estándar: 100m * 10.0 = 1000
    edge_std = G_procesado[3][4][0]
    expected_std = 100.0 * RISK_PROFILE["WEIGHTS"]["STANDARD"]
    assert edge_std['final_impedance'] == expected_std, f"Fallo en peso Estándar. Se obtuvo {edge_std['final_impedance']}"

print("✅ Todos los Tests Pasaron: La matemática es sólida.")