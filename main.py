import uvicorn
import logging
from fastapi import FastAPI, Depends, HTTPException, Request
from dotenv import load_dotenv
from typing import Optional
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from controllers.firebase import register_user_firebase, login_user_firebase
from controllers.moviescatalog import get_movies_catalog, add_movie
from models.userregister import UserRegister
from models.userlogin import UserLogin
from models.moviescatalog import MovieCatalog
from utils.security import decode_jwt_token
from utils.telemetry import init_telemetry, instrument_fastapi_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting up...")
    yield
    logger.info("API shutting down...")

app = FastAPI(
    title="Movies API",
    version="1.0.0",
    lifespan=lifespan,
)

try:
    telemetry_ok = init_telemetry()
    if telemetry_ok:
        instrument_fastapi_app(app)
        logger.info("Telemetry enabled and FastAPI instrumented.")
    else:
        logger.warning("Telemetry not enabled due to missing config.")
except Exception as e:
    logger.error(f"Telemetry initialization failed: {e}")

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user = decode_jwt_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    return user

@app.post("/signup")
async def signup(user: UserRegister):
    return await register_user_firebase(user)

@app.post("/login")
async def login(user: UserLogin):
    return await login_user_firebase(user)

@app.get("/catalog")
async def catalog(category: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    return await get_movies_catalog(category)

@app.post("/catalog")
async def create_movie(
    movie: MovieCatalog,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return await add_movie(movie=movie, request=request)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "Welcome to the Movies API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")