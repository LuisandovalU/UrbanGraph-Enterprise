# UrbanGraph Enterprise 🚀

### Ecosistema de Análisis Topológico Dinámico | Fórmula Sandoval 

UrbanGraph Enterprise es una plataforma geoespacial de misión crítica diseñada para la optimización de rutas peatonales seguras mediante inteligencia artificial, datos cinéticos (clima) y arquitectura de microservicios.

---

## Arquitectura Enterprise

El sistema está completamente contenerizado y desacoplado:

1.  **Motor Sandoval (`engine.py`)**: Núcleo de inteligencia con soporte para pesos cinéticos (clima/eventos).
2.  **API Segura (`main.py`)**: Basada en FastAPI con seguridad **OAuth2 Bearer Token**.
3.  **UI Interactiva (`5_app_web.py`)**: Dashboard ligero para visualización topológica.
4.  **Infraestructura Docker**: Orquestación mediante `docker-compose` para escalabilidad global.
5.  **CI/CD Pipeline**: Validación automática de lógica y seguridad mediante GitHub Actions.

---

## API Reference & Segurida

La API está protegida. Para realizar consultas, se requiere el Bearer Token corporativo.

- **Base URL**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Token de Acceso**: `sandoval-enterprise-token-2025`

### `POST /v1/route/safe`
Calcula la ruta óptima considerando factores estáticos de riesgo y dinámicos (clima).

**Body:**
```json
{
  "origin": [19.4146, -99.1697],
  "destination": [19.4206, -99.1626],
  "weather_condition": "rainy"
}
```

**Respuesta:**
- `distance_m`: Longitud real.
- `ai_explanation`: Explicación generada por el Asistente UrbanGraph.
- `spatial_status`: Estado de sincronización PostGIS.

---

##  Despliegue con Docker

Para lanzar el ecosistema completo en modo producción:

```bash
docker-compose up --build
```

Esto levantará:
- **API**: Puerto 8000
- **Web App**: Puerto 8501

---

## Créditos
Desarrollado por **Luis Sandoval | UPIICSA 2025**.
"Inteligencia topológica para un mundo en movimiento."
