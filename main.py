from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Tuple
import engine

# Simulación de Seguridad Enterprise
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_token(token: str = Depends(oauth2_scheme)):
    if token != "sandoval-enterprise-token-2025":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de API inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

app = FastAPI(
    title="UrbanGraph API",
    description="Motor de Análisis Topológico para Rutas Seguras (Fórmula Sandoval)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Modelo de datos para la solicitud con validación robusta
class RouteRequest(BaseModel):
    origin: Tuple[float, float] = Field(..., description="(lat, lon) del origen", example=(19.4146, -99.1697))
    destination: Tuple[float, float] = Field(..., description="(lat, lon) del destino", example=(19.4206, -99.1626))
    weather_condition: str = Field("clear", description="Condición climática (clear, rainy, flooded)")

    @property
    def weather_factor(self):
        factors = {"clear": 1.0, "rainy": 1.5, "flooded": 3.0}
        return factors.get(self.weather_condition.lower(), 1.0)

    @property
    def valid_coords(self):
        for lat, lon in [self.origin, self.destination]:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return False
        return True

# Modelo de datos para la respuesta
class RouteResponse(BaseModel):
    distance_m: float
    route_nodes: List[int]
    origin_node: int
    destination_node: int
    ai_explanation: str = Field(..., description="Explicación generada por el Asistente Sandoval")
    spatial_status: str = Field("PostGIS Native", description="Estado de sincronización espacial")

# Cargar y procesar el grafo global al iniciar (singleton para eficiencia)
G_base = engine.cargar_grafo_seguro()
G_processed = engine.aplicar_formula_sandoval(G_base)

@app.get("/")
def read_root():
    return {"message": "UrbanGraph Engine API is online", "status": "operational"}

@app.post("/v1/route/safe", response_model=RouteResponse)
async def get_safe_route(request: RouteRequest, token: str = Depends(verify_token)):
    """
    Calcula una ruta optimizada para seguridad basada en la Fórmula Sandoval.
    Requiere autenticación Bearer Token.
    """
    if not request.valid_coords:
        raise HTTPException(status_code=400, detail="Coordenadas geográficas inválidas (fuera de rango).")
    
    try:
        # Reprocesar pesos dinámicos según el clima solicitado
        # NOTA: En producción, usaríamos un middleware para no reprocesar todo el grafo en cada request
        G_local = engine.aplicar_formula_sandoval(G_processed, weather_impact=request.weather_factor)
        
        ruta, n_orig, n_dest = engine.calcular_ruta_optima(
            G_local, 
            request.origin, 
            request.destination, 
            criterio='final_impedance'
        )
        
        # Calcular distancia real de esta ruta
        import networkx as nx
        distancia = nx.shortest_path_length(G_local, n_orig, n_dest, weight='length')
        
        # Placeholder para explicación de IA (LLM Integration)
        clima_msg = "lluvia intensa" if request.weather_factor > 1.0 else "cielo despejado"
        explicacion = f"Análisis Sandoval: Ruta optimizada para {clima_msg}. Se priorizaron corredores seguros."
        
        return RouteResponse(
            distance_m=distancia,
            route_nodes=ruta,
            origin_node=n_orig,
            destination_node=n_dest,
            ai_explanation=explicacion
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
