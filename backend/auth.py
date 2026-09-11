import bcrypt
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import models

SECRET_KEY = "temporary-secret-key-for-learning-change-this-later"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_email(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> str:
    """Decodes the JWT token and returns the user's email if valid, otherwise raises an error."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

def require_doctor(current_user_email: str, db) -> models.User:
    """Checks that the current user is a verified doctor. Raises an error if not."""
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this")
    return user

def require_admin(current_user_email: str, db) -> models.User:
    """Checks that the current user is an admin. Raises an error if not."""
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access this")
    return user