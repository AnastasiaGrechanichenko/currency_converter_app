from datetime import datetime, timezone, timedelta
from typing import Annotated
import jwt
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import settings,SessionLocal
from app import models
# Настройка хэширования
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_password_hash(password:str):
    return pwd_context.hash(password)

def verify_passoword(plain_password:str, hashed_password:str):
    return pwd_context.verify(plain_password,hashed_password)

# Создание jwt-токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data:dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc)+timedelta(
        minutes=settings.access_token_expire_minutes
    )

    to_encode.update({"exp":expire})

    encoded_jwt=jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm= settings.algorithm
    )
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

