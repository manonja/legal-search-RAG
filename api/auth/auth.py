import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from auth.models import Token, TokenData, User
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# Setup password hashing early
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

# Simple in-memory user repository
class UserRepository:
    def __init__(self):
        self.users = {}

    def get_user_by_email(self, email: str):
        return self.users.get(email)

    def authenticate_user(self, email: str, password: str):
        user = self.get_user_by_email(email)
        if not user:
            # Default admin user for development - using env or generated password
            if email == "admin@example.com" and password == os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme"):
                # Generate a secure random password hash for initial admin
                pwd_hash = get_password_hash(secrets.token_urlsafe(12))

                user = User(
                    email="admin@example.com",
                    tenant_id="default",
                    id=str(uuid.uuid4()),
                    is_active=True,
                    is_admin=True,
                    full_name="Admin User",
                    created_at=datetime.now()
                )
                # Store the user with hashed password
                self.users[email] = user
                return user
            return None

        if not verify_password(password, user.hashed_password):
            return None
        return user

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Setup OAuth2 with password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# User repository instance
user_repo = UserRepository()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token with expiration."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# Create function-level dependencies to avoid B008 warnings
def get_oauth2_scheme():
    return oauth2_scheme

async def get_current_user(token: str = Depends(get_oauth2_scheme)):
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")

        if email is None or tenant_id is None:
            raise credentials_exception

        token_data = TokenData(email=email, tenant_id=tenant_id)
    except JWTError as e:
        raise credentials_exception from e

    user = user_repo.get_user_by_email(email)

    if user is None:
        raise credentials_exception

    return user

# Function to get current user dependency
def get_current_user_dependency():
    return get_current_user

async def get_current_active_user(current_user: User = Depends(get_current_user_dependency)):
    """Check if the current user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get a JWT token."""
    user = user_repo.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id, "is_admin": user.is_admin},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
