import json
import logging
from fastapi import HTTPException, Request
from typing import Optional

from utils.database import execute_query_json
from utils.redis_cache import get_redis_client, get_from_cache, store_in_cache
from models.moviescatalog import MovieCatalog
from utils.security import validateadmin

logger = logging.getLogger(__name__)

MOVIES_CACHE_KEY = "movies:catalog:all"
CACHE_TTL = 1800

redis_client = get_redis_client()

async def get_movies_catalog(category: Optional[str] = None):
    """
    Obtiene el catálogo de películas, con cache en Redis usando categoría.
    """
    if not redis_client:
        logger.warning("Redis no disponible, consulta directa a BD.")

    cache_key = MOVIES_CACHE_KEY
    query = "SELECT movieId, title, genres FROM cinema.movies"
    params = ()

    if category:
        category_lower = category.lower()
        cache_key = f"movies:catalog:{category_lower}"
        query += " WHERE LOWER(genres) LIKE ?"
        params = (f"%{category_lower}%",)
    cached_data = get_from_cache(redis_client, cache_key) if redis_client else None
    if cached_data is not None:
        logger.info(f"Cache hit para key: {cache_key}")
        return cached_data

    try:
        result_json = await execute_query_json(query, params)
        data = json.loads(result_json)
        if redis_client:
            store_in_cache(redis_client, cache_key, data, CACHE_TTL)

        return data
    except Exception as e:
        logger.error(f"Error al obtener catálogo: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener catálogo: {str(e)}")


@validateadmin
async def add_movie(request: Request, movie: MovieCatalog):
    """
    Inserta una nueva película y elimina la cache asociada.
    """
    redis_client = get_redis_client()
    if redis_client is None:
        logger.warning("Redis no disponible, continuará sin caché.")
    query_insert = """
        INSERT INTO cinema.movies (title, genres)
        OUTPUT INSERTED.movieId
        VALUES (?, ?)
    """
    params = (movie.title, movie.genres)

    try:
        result_json = await execute_query_json(query_insert, params, needs_commit=True)
        inserted_result = json.loads(result_json)

        if not inserted_result or "movieId" not in inserted_result[0]:
            raise HTTPException(status_code=500, detail="No se pudo obtener el ID insertado.")
        inserted_id = inserted_result[0]["movieId"]
        logger.info(f"Película insertada con ID {inserted_id}")

        if redis_client:
            redis_client.delete(MOVIES_CACHE_KEY)
            logger.info(f"Cache invalidado: {MOVIES_CACHE_KEY}")

            if movie.genres:
                genres = [g.strip().lower() for g in movie.genres.split(",")]
                for genre in genres:
                    key = f"movies:catalog:{genre}"
                    redis_client.delete(key)
                    logger.info(f"Cache invalidado: {key}")

        movie.movieId = inserted_id
        return {"message": "Película agregada correctamente.", "movie": movie.dict()}

    except Exception as e:
        logger.error(f"Error al agregar película: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al agregar película: {str(e)}")