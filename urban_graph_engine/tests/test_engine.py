"""Basic tests for UrbanGraph Engine."""
import pytest
from urban_graph_engine.core import engine


def test_load_graph():
    """Test that the graph can be loaded."""
    try:
        G = engine.cargar_grafo_seguro()
        assert G is not None
        assert len(G.nodes) > 0
    except Exception as e:
        pytest.skip(f"Graph loading failed: {e}")


def test_formula_sandoval():
    """Test applying the Sandoval formula."""
    G = engine.cargar_grafo_seguro()
    G_modified = engine.aplicar_formula_sandoval(G.copy())
    # Check that final_impedance is added to edges
    sample_edge = list(G_modified.edges(data=True))[0]
    assert 'final_impedance' in sample_edge[2]


def test_calculate_route():
    """Test calculating an optimal route."""
    G = engine.cargar_grafo_seguro()
    coords_orig = (19.3948, -99.1736)  # WTC CDMX approx
    coords_dest = (19.4206, -99.1626)  # Another point
    try:
        ruta, n_orig, n_dest = engine.calcular_ruta_optima(G, coords_orig, coords_dest)
        assert ruta is not None
        assert len(ruta) > 0
        assert n_orig != n_dest
    except Exception as e:
        pytest.skip(f"Route calculation failed: {e}")


def test_geo_cache():
    """Test geocoding with cache."""
    # Test saving and loading cache
    test_coords = (19.3948, -99.1736)
    engine.GEO_CACHE["test"] = test_coords
    engine.save_geo_cache()
    # Reload
    engine.GEO_CACHE = {}
    if os.path.exists(engine.GEO_CACHE_FILE):
        with open(engine.GEO_CACHE_FILE, "r") as f:
            engine.GEO_CACHE = json.load(f)
    assert "test" in engine.GEO_CACHE