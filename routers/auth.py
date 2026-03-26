"""
Router de autenticación JWT para Operations Dashboard
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User


# Configuración de seguridad
SECRET_KEY = "ops-dashboard-secret-key-change-in-production-2024"  # TODO: Mover a variable de entorno
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 días

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class TokenData(BaseModel):
    username: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    team_id: Optional[int]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Utilidades
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password contra hash bcrypt"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashea password con bcrypt"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autentica usuario por username + password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    # Si el password no está hasheado (seed inicial), hacer hash
    if not user.hashed_password or not user.hashed_password.startswith("$2b$"):
        # Plain text password - comparar directamente
        if user.hashed_password == password:
            # Migrar a bcrypt hash
            try:
                user.hashed_password = get_password_hash(password)
                db.commit()
            except Exception:
                # Si falla hash, dejar como está por ahora
                pass
            return user
        return None
    
    # Verificar contra bcrypt hash
    try:
        if not verify_password(password, user.hashed_password):
            return None
    except Exception:
        # Hash corrupto o inválido - rechazar
        return None
    
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency que obtiene el usuario actual desde JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    if not user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency que valida que el usuario esté activo"""
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(allowed_roles: list[str]):
    """Dependency factory para verificar roles"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# Endpoints
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de login OAuth2 compatible
    
    - **username**: Username del usuario
    - **password**: Contraseña (se valida contra bcrypt hash)
    
    Retorna JWT token válido por 7 días
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "team_id": user.team_id
        }
    }


@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Obtiene información del usuario actual (desde JWT token)
    
    Requiere: Bearer token válido en header Authorization
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresca el JWT token del usuario actual
    
    Requiere: Bearer token válido (puede estar próximo a expirar)
    Retorna: Nuevo token con 7 días de validez
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username, "role": current_user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "team_id": current_user.team_id
        }
    }


# Middleware helper para proteger endpoints
def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency que requiere rol admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_leader_or_admin(current_user: User = Depends(get_current_user)):
    """Dependency que requiere rol leader o admin"""
    if current_user.role not in ["admin", "leader"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leader or Admin access required"
        )
    return current_user


@router.post("/bootstrap")
async def bootstrap_admin(db: Session = Depends(get_db)):
    """
    TEMPORAL: Crea usuario admin inicial si no existe ninguno
    
    Este endpoint NO requiere autenticación y solo funciona si:
    1. No existe ningún usuario admin en la DB
    2. Se ejecuta exactamente UNA vez
    
    **ELIMINAR en producción después del bootstrap inicial**
    """
    # Verificar si ya existe algún admin
    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin:
        raise HTTPException(
            status_code=400,
            detail="Admin user already exists. Bootstrap not needed."
        )
    
    # Crear usuario admin inicial
    admin_user = User(
        username="padawan",
        email="padawan@ops.dev",
        full_name="Padawan (Bootstrap Admin)",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        team_id=None,  # Sin equipo por ahora
        active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return {
        "message": "✅ Bootstrap admin created successfully",
        "username": admin_user.username,
        "note": "DELETE /auth/bootstrap endpoint after first use"
    }
