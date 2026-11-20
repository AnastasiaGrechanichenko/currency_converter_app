from datetime import datetime
from typing import Annotated
import jwt
from passlib.context import CryptContext
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import settings,SessionLocal
from app import models
