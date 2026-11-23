from datetime import datetime, timezone, timedelta
from typing import Annotated
import jwt
from dns.dnssecalgs import algorithms
from passlib.context import Cryptcontext
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

# Проверка токена
def get_current_user(
        token:Annotated[str,Depends(oauth2_scheme)],
        db:Annotated[Session,Depends(get_db)]
)-> models.User:
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate":"Bearer"}
    )
    # Здесь происходит расшифровка токена
    try:
        payload = jwt.encode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        user_id_str: str|None=payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек",
            headers={"WWW-Authenticate":"Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id==user_id).first()

    if user is None:
        raise credentials_exception
    return user
