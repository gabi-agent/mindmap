from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as DBSession
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# Password hashing - using pbkdf2_sha256 to avoid bcrypt 72-byte limit
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT Configuration - Load from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-only-for-testing")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

# OAuth2 Password Bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: DBSession = Depends(get_db)) -> Optional[models.User]:
    if not token:
        return None
    
    payload = verify_token(token)
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user is None:
        return None
    
    return user

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def register(request: Request, user: schemas.UserRegister, db: DBSession = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = pwd_context.hash(user.password)
    
    # Create user
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=password_hash
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=schemas.LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, user: schemas.UserLogin, db: DBSession = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    return schemas.LoginResponse(
        access_token=access_token,
        user=schemas.UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            created_at=db_user.created_at
        )
    )

@router.post("/logout")
async def logout(current_user: models.User = Depends(get_current_user)):
    # In a real app with token blacklist, we would invalidate token here
    # For now, client just removes token from localStorage
    return {"message": "Logout successful"}
