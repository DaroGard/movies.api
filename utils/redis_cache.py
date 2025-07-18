import os
import json
import logging
import redis
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_CONNECTION_STRING")

def get_redis_client() -> Optional[redis.Redis]:
    if not REDIS_URL:
        logger.error("La variable de entorno REDIS_CONNECTION_STRING no está definida.")
        return None

    try:
        client = redis.from_url(
            REDIS_URL,
            decode_responses=True
        )
        client.ping()
        logger.info("✅ Conectado exitosamente a Redis usando Connection String")
        return client
    except Exception as e:
        logger.error(f"❌ Error al conectar a Redis con Connection String: {e}")
        return None

def get_from_cache(redis_client: Optional[redis.Redis], cache_key: str) -> Optional[Any]:
    if not redis_client:
        logger.info("ℹ Redis no disponible - lectura de caché omitida")
        return None

    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"✅ Cache hit para la clave: {cache_key}")
            return json.loads(cached_data)
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ Datos corruptos en caché para la clave '{cache_key}', eliminando: {str(e)}")
        redis_client.delete(cache_key)
    except Exception as e:
        logger.warning(f"⚠️ Fallo al obtener la clave '{cache_key}' desde caché: {str(e)}")

    return None

def delete_cache(redis_client: Optional[redis.Redis], cache_key: str) -> bool:
    if not redis_client:
        logger.info("ℹ Redis no disponible - eliminación de caché omitida")
        return False

    try:
        result = redis_client.delete(cache_key)
        if result:
            logger.info(f"🗑️ Clave de caché '{cache_key}' eliminada exitosamente")
            return True
        else:
            logger.info(f"ℹ Clave de caché '{cache_key}' no existía")
            return False
    except Exception as e:
        logger.warning(f"⚠️ Error al eliminar la clave de caché '{cache_key}': {str(e)}")
        return False

def store_in_cache(redis_client: Optional[redis.Redis], cache_key: str, data: list[dict], expiration: int) -> None:
    if not redis_client:
        logger.info("ℹ Redis no disponible - se omite almacenamiento en caché")
        return

    try:
        json_data = json.dumps(data, default=str)
        redis_client.setex(cache_key, expiration, json_data)
        logger.info(f"📦 Datos almacenados en caché con clave '{cache_key}' por {expiration} segundos")
    except Exception as e:
        logger.warning(f"⚠️ Fallo al almacenar datos en caché con clave '{cache_key}': {str(e)}")
