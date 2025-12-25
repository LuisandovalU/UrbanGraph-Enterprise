import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import json
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()


# --- Configuración de Logs ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("data_ingestor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataIngestor")

# --- Configuración de API ADIP & Telegram ---
ADIP_RESOURCE_ID = "59d5ede6-7af8-4384-a114-f84ff1b26fe1"
ADIP_URL = f"https://datos.cdmx.gob.mx/api/3/action/datastore_search?resource_id={ADIP_RESOURCE_ID}&limit=100"
FALLBACK_FILE = "realtime_fallback.json"
BACKUP_STATIC_FILE = "backup_data.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def fetch_adip_data():
    """Descarga datos de la API de Datos Abiertos de la CDMX."""
    try:
        response = requests.get(ADIP_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data["result"]["records"]
        else:
            logger.error("API ADIP respondió con error.")
            return None
    except Exception as e:
        logger.error(f"Error de conexión con ADIP: {e}")
        return None

def send_telegram_alert(incident_data):
    """Envía una alerta inmediata vía Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram no configurado. Ignorando alerta.")
        return

    msg = (
        f"⚠️ *ALERTA CRÍTICA: UrbanGraph Protocol*\n\n"
        f"*Incidente:* {incident_data.get('tipo', 'Desconocido')}\n"
        f"*Ubicación:* {incident_data.get('lat')}, {incident_data.get('lon')}\n\n"
        f"Activando Protocolo de Desvío Sandoval. Notificando a unidades en radio de 500m."
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    
    try:
        requests.post(url, json=payload, timeout=5)
        logger.info("Alerta de Telegram enviada con éxito.")
    except Exception as e:
        logger.error(f"Error enviando alerta de Telegram: {e}")

def check_active_routes_collision(incidents):
    """
    Misión 8: Cruza nuevos incidentes contra rutas activas.
    Para esta demo, simulamos la detección de colisión si el incidente
    cae dentro de zonas de alto tráfico.
    """
    for inc in incidents:
        # Lógica Sandoval: Si el incidente es de alto impacto, alertamos
        if inc.get("impacto", 0) >= 5.0:
            send_telegram_alert(inc)
            break # Evitamos spam para la demo


def process_data(records):
    """Limpia y procesa los datos usando Pandas y GeoPandas."""
    if not records:
        return None
    
    df = pd.DataFrame(records)
    
    # Limpieza básica
    # Se asume que las columnas son 'latitud' y 'longitud' basándose en la API de CDMX
    try:
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])
    except KeyError as e:
        logger.error(f"Columnas de coordenadas no encontradas: {e}")
        return None

    # Convertir a GeoDataFrame
    geometry = [Point(xy) for xy in zip(df['longitud'], df['latitud'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    
    # Estructura para UrbanGraph
    incidents = []
    for _, row in gdf.iterrows():
        incidents.append({
            "tipo": row.get("incidente_c4", "Incidente Vial"),
            "lat": row["latitud"],
            "lon": row["longitud"],
            "impacto": 5.0, # Impacto Sandoval 2.5
            "color": "red",
            "icon": "exclamation-triangle"
        })
    
    return incidents

def run_ingestor():
    """Ciclo principal de ingesta cada 15 minutos."""
    while True:
        logger.info("Iniciando ciclo de ingesta de datos ADIP...")
        records = fetch_adip_data()
        
        incidents = process_data(records)
        
        if incidents:
            # Misión 8: Alerta Temprana
            check_active_routes_collision(incidents)
            
            output = {

                "incidents": incidents,
                "last_sync": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "Healthy"
            }
            with open(FALLBACK_FILE, "w") as f:
                json.dump(output, f, indent=4)
            logger.info(f"Datos sincronizados. {len(incidents)} incidentes guardados en {FALLBACK_FILE}.")
        else:
            logger.warning("Fallo en ingesta. Manteniendo datos previos o usando backup estático.")
            if not os.path.exists(FALLBACK_FILE):
                if os.path.exists(BACKUP_STATIC_FILE):
                    logger.info("Cargando backup estático para inicializar fallback.")
                    with open(BACKUP_STATIC_FILE, "r") as f:
                        static_data = json.load(f)
                        with open(FALLBACK_FILE, "w") as f2:
                            json.dump(static_data, f2, indent=4)
                else:
                    logger.error("No se encontró backup_data.json para fallback inicial.")

        logger.info("Esperando 15 minutos para el siguiente ciclo...")
        time.sleep(15 * 60)

if __name__ == "__main__":
    run_ingestor()
