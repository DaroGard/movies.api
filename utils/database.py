import os
import pyodbc
import logging
import json
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

driver = os.getenv('SQL_DRIVER', 'ODBC Driver 18 for SQL Server')
server = os.getenv('SQLSERVER')
database = os.getenv('SQLDATABASE')
username = os.getenv('SQLUSER')
password = os.getenv('SQLPASSWORD')

connection_string = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)

async def get_db_connection():
    try:
        logger.info("Intentando conectar a la base de datos...")
        conn = pyodbc.connect(connection_string, timeout=10)
        logger.info("Conexión establecida exitosamente.")
        return conn
    except pyodbc.Error as e:
        logger.error(f"Error de conexión a la base de datos: {str(e)}")
        raise Exception(f"Error de conexión a la base de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado al conectar: {str(e)}")
        raise

async def execute_query_json(sql: str, params: tuple = None, needs_commit: bool = False):
    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()

        if params:
            logger.info(f"Ejecutando SQL con parámetros: {sql}")
            cursor.execute(sql, params)
        else:
            logger.info(f"Ejecutando SQL sin parámetros: {sql}")
            cursor.execute(sql)

        results = []
        if cursor.description:
            columns = [column[0] for column in cursor.description]
            logger.info(f"Columnas devueltas: {columns}")
            for row in cursor.fetchall():
                processed_row = [
                    str(item) if isinstance(item, (bytes, bytearray)) else item for item in row
                ]
                results.append(dict(zip(columns, processed_row)))
        else:
            logger.info("Consulta ejecutada sin columnas devueltas (INSERT/UPDATE/DELETE).")

        if needs_commit:
            logger.info("Realizando commit...")
            conn.commit()

        return json.dumps(results, default=str)

    except pyodbc.Error as e:
        logger.error(f"Error SQL (SQLSTATE {e.args[0]}): {str(e)}")
        if conn and needs_commit:
            try:
                logger.warning("Intentando rollback por error...")
                conn.rollback()
            except pyodbc.Error as rb_e:
                logger.error(f"Error durante rollback: {rb_e}")
        raise Exception(f"Error SQL: {str(e)}") from e

    except Exception as e:
        logger.error(f"Error inesperado en la consulta: {str(e)}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.info("Conexión cerrada.")