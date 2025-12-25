# --- URBANgraph Enterprise Multi-stage Build ---
# Stage 1: Dependency Builder
FROM python:3.9-slim as builder

WORKDIR /build
COPY requirements.txt .
# Install build dependencies for spatial libs if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    g++ \
    libpq-dev \
    && pip install --user --no-cache-dir -r requirements.txt


# Stage 2: Production Runtime
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Environments for performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Ports: API (8000), WebApp (8501)
EXPOSE 8000
EXPOSE 8501

# Command is overridden by docker-compose for each service
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
