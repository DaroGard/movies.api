import os
import json
import logging
import firebase_admin
import requests
import traceback

from fastapi import HTTPException
from firebase_admin import credentials, auth as firebase_auth, _auth_utils
from dotenv import load_dotenv

from utils.database import execute_query_json
from utils.security import create_jwt_token
from models.userregister import UserRegister
from models.userlogin import UserLogin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

if not firebase_admin._apps:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.getenv("FIREBASE_CRED_PATH")
        full_cred_path = os.path.normpath(os.path.join(base_dir, cred_path))

        if not os.path.isfile(full_cred_path):
            raise FileNotFoundError(f"No se encontró archivo de credenciales Firebase: {full_cred_path}")

        cred = credentials.Certificate(full_cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase inicializado correctamente.")
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {e}")
        raise HTTPException(status_code=500, detail="No se pudo inicializar Firebase")

async def register_user_firebase(user: UserRegister) -> dict:
    user_record = None
    try:
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password
        )
        logger.info(f"Usuario creado en Firebase: {user.email}")
    except _auth_utils.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="El correo ya existe en Firebase.")
    except Exception as e:
        logger.exception("Error al crear usuario en Firebase")
        raise HTTPException(status_code=400, detail=f"Error al registrar usuario: {e}")
    query = """
        EXEC cinema.users_insert ?, ?, ?, ?
    """
    params = (
        user_record.uid,
        user.email,
        user.is_admin,
        user.is_active
    )
    try:
        result_json = await execute_query_json(query, params, needs_commit=True)
        logger.info(f"Usuario insertado en SQL Server: {user.email}")
        custom_token = firebase_auth.create_custom_token(user_record.uid).decode('utf-8')
        return {
            "message": "Usuario creado e insertado correctamente.",
            "firebase_custom_token": custom_token
        }
    except Exception as e:
        logger.error(f"Error en base de datos al insertar usuario {user.email}: {e}", exc_info=True)
        firebase_auth.delete_user(user_record.uid)
        raise HTTPException(status_code=500, detail=f"Error al insertar en base de datos: {str(e)}")

async def login_user_firebase(user: UserLogin):
    api_key = os.getenv("FIREBASE_API_KEY")
    if not api_key:
        logger.error("API Key de Firebase no configurada")
        raise HTTPException(status_code=500, detail="API Key de Firebase no configurada")

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": user.email,
        "password": user.password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.warning(f"Error de autenticación para {user.email}: {e}")
        raise HTTPException(status_code=400, detail="Credenciales inválidas.")
    except Exception as e:
        logger.exception("Error al autenticar con Firebase")
        raise HTTPException(status_code=500, detail="Error al autenticar con Firebase.")

    query = """
        SELECT uid, email, is_active, is_admin
        FROM cinema.users
        WHERE email = ?
    """

    try:
        result_json = await execute_query_json(query, (user.email,))
        logger.debug(f"Resultado JSON de la consulta: {result_json} (tipo: {type(result_json)})")

        result = json.loads(result_json)
        user_data = result[0]

        if not user_data["is_active"]:
            raise HTTPException(status_code=403, detail="Usuario inactivo")

        token = create_jwt_token(
            email=user_data["email"],
            active=user_data["is_active"],
            admin=user_data["is_admin"]
        )

        return {
            "message": "Usuario autenticado exitosamente",
            "token": token
        }
    except IndexError:
        logger.warning(f"Usuario no encontrado en base de datos para email: {user.email}")
        raise HTTPException(status_code=404, detail="Usuario no encontrado en base de datos.")
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear JSON: {e}, contenido recibido: {result_json}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno: JSON inválido.")
    except Exception as e:
        tb_str = traceback.format_exc()
        logger.error(f"Error inesperado: {str(e)}\nTraceback:\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")