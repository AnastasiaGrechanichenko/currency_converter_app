from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url:str = "postgresql://postgres@localhost:5432/currency_db"
    exchange_api_url:str ="https://open.er-api.com/v6/latest/USD"
    redis_host: str ="localhost"
    redis_port: int = 6379
    class Config:
        env_file =".env"

settings = Settings()

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

def check_db_connection() ->bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
