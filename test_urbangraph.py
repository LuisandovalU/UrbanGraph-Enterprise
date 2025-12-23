import networkx as nx
import engine

def test_pesos_del_algoritmo():
    """
    Verifica que la Función de Costo Sandoval 2.4 (Enterprise) aplique 
    correctamente la matemática de compromiso entre tiempo y riesgo.
    """
    # 1. Setup: Crear un Grafo Simulado (Mock)
    G = nx.MultiDiGraph()
    
    # Agregar Arista A: Calle Segura (ej. Colima)
    G.add_edge(1, 2, key=0, length=100.0, name='Calle Colima')
    
    # Agregar Arista B: Zona de Peligro (ej. Insurgentes) -> Disparará avenue_bonus 0.6
    G.add_edge(2, 3, key=0, length=100.0, name='Av Insurgentes Sur')
    
    # Agregar Arista C: Calle Estándar (Nombre X)
    G.add_edge(3, 4, key=0, length=100.0, name='Calle X')

    # 2. Ejecución: Correr la lógica desde el motor (Default: h_ratio=0.5, s_ratio=0.5)
    G_procesado = engine.aplicar_formula_sandoval(G)

    # 3. Aserción: Verificar la Matemática Enterprise 2.4
    # Fórmula: (L * avenue_bonus * micro_bonus * 0.5) + (L * W * 0.5 * 5.0 * 0.5)
    
    # Caso Seguro: (100 * 1 * 1 * 0.5) + (100 * 1.0 * 1.25) = 50 + 125 = 175.0
    edge_safe = G_procesado[1][2][0]
    expected_safe = 175.0
    assert edge_safe['final_impedance'] == expected_safe, f"Fallo en peso Seguro. Se obtuvo {edge_safe['final_impedance']}"

    # Caso Peligro: (100 * 0.6 * 0.5) + (100 * 50.0 * 1.25) = 30 + 6250 = 6280.0
    edge_danger = G_procesado[2][3][0]
    expected_danger = 6280.0
    assert edge_danger['final_impedance'] == expected_danger, f"Fallo en peso Peligro. Se obtuvo {edge_danger['final_impedance']}"

    # Caso Estándar: (100 * 0.5) + (100 * 10.0 * 1.25) = 50 + 1250 = 1300.0
    edge_std = G_procesado[3][4][0]
    expected_std = 1300.0
    assert edge_std['final_impedance'] == expected_std, f"Fallo en peso Estándar. Se obtuvo {edge_std['final_impedance']}"

if __name__ == "__main__":
    try:
        test_pesos_del_algoritmo()
        print("✅ UrbanOS 2040: Todos los Tests de Integridad Táctica pasaron.")
    except AssertionError as e:
        print(f"❌ Fallo en la verificación táctica: {e}")
        exit(1)