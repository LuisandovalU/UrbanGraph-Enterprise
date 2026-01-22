"""Tests for ingestor module."""
import pytest
from urban_graph_engine.services import ingestor
import os

def test_fetch_adip_data():
    """Test fetching ADIP data (mock or skip if API down)."""
    data = ingestor.fetch_adip_data()
    if data is None:
        pytest.skip("ADIP API not available")
    assert isinstance(data, list)

def test_process_data():
    """Test processing ADIP records."""
    sample_records = [
        {"latitud": 19.4, "longitud": -99.17, "incidente_c4": "Test"}
    ]
    incidents = ingestor.process_data(sample_records)
    assert incidents is not None
    assert len(incidents) == 1
    assert incidents[0]["lat"] == 19.4