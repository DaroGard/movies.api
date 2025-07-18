import os
import jwt
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from jwt import PyJWTError
from functools import wraps
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_jwt_token(email: str, active: bool, admin: bool, expires_hours=1):
    try:
        expiration = datetime.utcnow() + timedelta(hours=expires_hours)
        payload = {
            "email": email,
            "active": active,
            "admin": admin,
            "exp": expiration,
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        logger.error(f"Error al crear el token JWT: {e}")
        raise

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido.")

def validate(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            raise HTTPException(status_code=400, detail="Objeto request no encontrado.")

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Encabezado de autorización faltante.")

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Esquema de autenticación inválido.")
            payload = decode_jwt_token(token)

            if not payload.get("active"):
                raise HTTPException(status_code=403, detail="Usuario inactivo.")

            request.state.email = payload.get("email")

            return await func(*args, **kwargs)
        except ValueError:
            raise HTTPException(status_code=401, detail="Formato de token inválido.")
    return wrapper

def validateadmin(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            raise HTTPException(status_code=400, detail="Objeto request no encontrado.")

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Encabezado de autorización faltante.")

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Esquema de autenticación inválido.")
            payload = decode_jwt_token(token)

            if not payload.get("active"):
                raise HTTPException(status_code=403, detail="Usuario inactivo.")

            if not payload.get("admin"):
                raise HTTPException(status_code=403, detail="Permisos de administrador requeridos.")

            request.state.email = payload.get("email")

            return await func(*args, **kwargs)
        except ValueError:
            raise HTTPException(status_code=401, detail="Formato de token inválido.")
    return wrapper