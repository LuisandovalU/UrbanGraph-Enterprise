import networkx as nx
import engine

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

    # 2. Ejecución: Correr la lógica desde el motor
    G_procesado = engine.aplicar_formula_sandoval(G)

    # 3. Aserción: Verificar la Matemática
    weights = engine.RISK_PROFILE["WEIGHTS"]
    
    # Caso Seguro: 100m * 1.0 = 100
    edge_safe = G_procesado[1][2][0]
    expected_safe = 100.0 * weights["SAFE"]
    assert edge_safe['final_impedance'] == expected_safe, f"Fallo en peso Seguro. Se obtuvo {edge_safe['final_impedance']}"

    # Caso Peligro: 100m * 50.0 = 5000
    edge_danger = G_procesado[2][3][0]
    expected_danger = 100.0 * weights["DANGER"]
    assert edge_danger['final_impedance'] == expected_danger, f"Fallo en peso Peligro. Se obtuvo {edge_danger['final_impedance']}"

    # Caso Estándar: 100m * 10.0 = 1000
    edge_std = G_procesado[3][4][0]
    expected_std = 100.0 * weights["STANDARD"]
    assert edge_std['final_impedance'] == expected_std, f"Fallo en peso Estándar. Se obtuvo {edge_std['final_impedance']}"

if __name__ == "__main__":
    try:
        test_pesos_del_algoritmo()
        print("✅ Todos los Tests Pasaron: La matemática es sólida.")
    except AssertionError as e:
        print(f"❌ Fallo en la verificación: {e}")
        exit(1)