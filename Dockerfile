# Usar una imagen base de Python ligera
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y habilitar salida en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema para OSMnx y GDAL
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    libproj-dev \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer los puertos (8000 para API, 8501 para Streamlit)
EXPOSE 8000
EXPOSE 8501

# El comando por defecto se sobreescribirá en docker-compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
