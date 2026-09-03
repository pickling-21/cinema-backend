from pydantic import BaseModel
from src.core.config import settings


class JWTSettings(BaseModel):
    # in token
    authjwt_secret_key: str = settings.jwt_secret_key
    authjwt_access_token_expires: int = settings.jwt_access_expire_minutes * 60
    authjwt_refresh_token_expires: int = settings.jwt_refresh_expire_days * 24 * 60 * 60
