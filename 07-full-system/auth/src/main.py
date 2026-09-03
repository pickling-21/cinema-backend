from src.db.postgres import create_database
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from src.core.config import settings
from fastapi.responses import ORJSONResponse
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from src.core.jwt_config import JWTSettings
from async_fastapi_jwt_auth import AuthJWT
from src.api.v1.auth import router as auth_router
from src.api.v1.roles import router as roles_router
from src.db import redis_db


@AuthJWT.load_config
def get_config():
    return JWTSettings()


# OpenTelemetry / Jaeger setup
def setup_tracing(app: FastAPI):
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=settings.jaeger_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


# Rate Limiter configuration
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_database()

    redis_db.redis = Redis.from_url(str(settings.redis_dsn))
    yield
    if redis_db.redis:
        await redis_db.redis.close()


app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации и авторизации",
    version="0.1.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    redirect_slashes=False,
)

setup_tracing(app)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware('http')
async def before_request(request: Request, call_next):
    response = await call_next(request)
    request_id = request.headers.get('X-Request-Id')
    if not request_id:
        return ORJSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'detail': 'X-Request-Id is required'})
    return response


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    """
    Вместо 500 возвращаем понятную ошибку
    """
    return ORJSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/")
async def root():
    return {"message": "Auth Service is running."}


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(roles_router, prefix="/api/v1/roles", tags=["roles"])
