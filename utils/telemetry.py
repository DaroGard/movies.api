import os
import logging
from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = logging.getLogger(__name__)

def init_telemetry():
    try:
        load_dotenv(override=True)
        connection_string = os.getenv("APPINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logger.warning("Connection string de Application Insights no encontrada en .env")
            return False
        service_name = os.getenv("DTEL_SERVICE_NAME", "Movies_API")
        configure_azure_monitor(
            connection_string=connection_string,
            service_name=service_name,           
            enable_live_metrics=True,
            enable_standard_metrics=True
        )
        logger.info(f"Application Insights configurado correctamente con service_name: {service_name}")
        return True

    except Exception as e:
        logger.error(f"Error al configurar Application Insights: {e}")
        raise

def instrument_fastapi_app(app):
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentado para telemetría Azure")
    except Exception as e:
        logger.error(f"No se pudo instrumentar FastAPI: {e}")