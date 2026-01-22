# Estructura Propuesta del Proyecto

- Objetivo: separar código, datos y recursos para facilitar el mantenimiento y escalabilidad.
- Alcance: skeleton inicial para un layout limpio; migración progresiva de código existente.

## Árbol de directorios recomendado
```
urban_graph_engine/
├── src/
│   └── urban_graph_engine/
│       ├── __init__.py
│       ├── cli.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── (módulos de lógica principal: graph/engine/etc.)
│       ├── io/
│       │   ├── __init__.py
│       │   └── (módulos de carga/exportación)
│       ├── services/
│       │   ├── __init__.py
│       │   └── (lógica de ingesta/actualización)
│       └── utils/
├── data/
├── tests/
├── docs/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── requirements.txt
```

- Notas: este layout facilita pruebas y versionado; las rutas deben ser importadas con el src-layout.

## Guía de desarrollo
- **Instalación**: `pip install -e .` desde `urban_graph_engine/`
- **Linting y formateo**: `urban-graph lint` o manual con black, isort, flake8
- **Pruebas**: `urban-graph test` o `pytest tests/`
- **Pre-commit**: Instala con `pre-commit install` para hooks automáticos
- **CI**: Ver `.github/workflows/ci.yml` para pipeline en GitHub
- **Ejemplo de uso**: Ejecuta `python scripts/example_usage.py` para ver cálculo de rutas básico

## Siguientes pasos sugeridos
- Completar la migración progresiva de código existente hacia src/urban_graph_engine.*
- Configurar herramientas (Black, isort, flake8) y pruebas (pytest).
- Añadir un CLI funcional que consuma la lógica del motor desde core/.
