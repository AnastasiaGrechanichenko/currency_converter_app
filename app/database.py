from sqlalchemy import create_engine,text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeBase
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url:str = "postgresql://postgres@localhost:5432/currency_db"
    exchange_api_url:str ="https://open.er-api.com/v6/latest/USD"
    redis_host: str ="localhost"
    redis_port: int = 6379

    secret_key: str ="super-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    class Config:
        env_file =".env"

settings = Settings()

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()

def check_db_connection() ->bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
