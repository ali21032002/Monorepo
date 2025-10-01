import os
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _env = os.getenv("ENV_FILE") or find_dotenv(usecwd=True)
    if _env:
        load_dotenv(_env)
except Exception:
    pass

# CORS
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
ALLOW_ORIGIN_REGEX = os.getenv("ALLOW_ORIGIN_REGEX")

# Database
DATABASE_URL = os.getenv("USER_DB_URL", os.getenv("DATABASE_URL", "sqlite:///./users.db"))

# Security
SECRET_KEY = os.getenv("USER_JWT_SECRET", os.getenv("JWT_SECRET", "change_me_in_prod"))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


