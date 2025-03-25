import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Base model for tenant data"""
    name: str
    description: Optional[str] = None

class TenantCreate(TenantBase):
    """Model for creating a new tenant"""
    admin_email: str

class Tenant(TenantBase):
    """Full tenant model including system fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    active: bool = True

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """Base user information"""
    email: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """Model for user creation"""
    password: str
    tenant_id: str

class User(UserBase):
    """Full user model with system fields"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Data encoded in JWT token"""
    email: str
    tenant_id: str
    is_admin: bool = False
