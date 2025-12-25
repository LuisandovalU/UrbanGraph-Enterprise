from fastapi import FastAPI, Header, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
import engine
import logging
import time

# --- Configuration & Security ---
API_KEY = "SANDOVAL-ENGINE-PRO-2040"
api_key_header = APIKeyHeader(name="access_token", auto_error=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UrbanAPI")

app = FastAPI(
    title="URBANgraph Enterprise",
    description="Intelligence-Driven Logistics & Integrity Engine. Soli Deo Gloria.",
    version="1.1.0"
)

# --- Global State: Safe Graph Loading ---
try:
    G_BASE = engine.cargar_grafo_seguro()
    logger.info("Enterprise Graph loaded successfully.")
except Exception as e:
    logger.critical(f"Failed to load base graph: {e}")
    G_BASE = None

# --- Models ---
class AnalyzeRequest(BaseModel):
    origin: str = Field(..., example="WTC Ciudad de México")
    destination: str = Field(..., example="Parque de los Venados")
    hurry_factor: float = Field(50.0, ge=0, le=100)

class RiskAnalysis(BaseModel):
    description: str
    risk_factors: List[str]
    impact_weights: Dict[str, float]
    recommendation_bi: str
    urban_stress_level: str

class RouteResponse(BaseModel):
    escudo: Optional[List[int]]
    relampago: Optional[List[int]]
    directa: Optional[List[int]]
    integrity_score: float
    quadrants: Dict[str, str]
    risk_analysis: RiskAnalysis

class HealthStatus(BaseModel):
    status: str
    engine: str
    integrity_check: str
    timestamp: str

# --- Security Dependency ---
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid access_token")
    return api_key

# --- Endpoints ---

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Returns operational status and 'Soli Deo Gloria' integrity check."""
    return {
        "status": "Operational",
        "engine": "Sandoval-v2.5",
        "integrity_check": "Soli Deo Gloria. Integrity Verified.",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/v1/analyze", response_model=RouteResponse)
async def analyze_route(request: AnalyzeRequest, _=Depends(get_api_key)):
    """Accepts origin/dest, returns 3 enterprise routes + integrity score."""
    if G_BASE is None:
        raise HTTPException(status_code=500, detail="Graph Engine Offline")
    
    try:
        # Geocoding via Engine Cache
        coords_orig = engine.geocode_with_cache(request.origin)
        coords_dest = engine.geocode_with_cache(request.destination)
        
        # Real-time Data Ingestion (Circuit Breaker)
        realtime = engine.fetch_realtime_data()
        
        # Multi-Route Analysis
        analysis = engine.obtener_analisis_multi_ruta(
            G_BASE, 
            coords_orig, 
            coords_dest, 
            hurry_factor=request.hurry_factor,
            realtime_data=realtime
        )
        
        return analysis
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/score")
async def get_confidence_score(lat: float, lon: float, _=Depends(get_api_key)):
    """Returns a 'Confidence Index' based on ADIP cameras and infrastructure density."""
    try:
        infra = engine.fetch_adip_infrastructure(lat, lon)
        score = engine.calculate_analytics_score([], G_BASE, infra)
        return score
    except Exception as e:
        logger.error(f"Score calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class IntegrityRequest(BaseModel):
    route_points: List[Tuple[float, float]] = Field(..., example=[(19.4188, -99.1609), (19.4208, -99.1566)])
    cargo_value_tier: Optional[str] = Field("STANDARD", enum=["STANDARD", "HIGH_VALUE", "HAZMAT"])

class Threat(BaseModel):
    type: str
    location: List[float]
    description: str

class DetailedBreakdown(BaseModel):
    incidents_impact: float
    historical_risk_impact: float
    sensitivity_multiplier: float

class IntegrityResponse(BaseModel):
    integrity_score: float
    urban_stress_level: str
    main_stressor: str
    recommendation: str
    detailed_breakdown: DetailedBreakdown
    detected_threats: List[Threat]
    alternative_safe_route: bool
    insurance_risk_factor: float


@app.post("/api/v1/integrity_check", response_model=IntegrityResponse)
async def integrity_check(request: IntegrityRequest, _=Depends(get_api_key)):
    """Evalúa el riesgo total de una ruta y sugiere alternativas."""
    if G_BASE is None:
        raise HTTPException(status_code=500, detail="Graph Engine Offline")
    
    try:
        result = engine.evaluar_integridad_ruta(request.route_points, request.cargo_value_tier, G_BASE)
        return result
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
