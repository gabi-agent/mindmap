from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime
from typing import Optional

# ===== User Schemas =====

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=6,
        max_length=72,
        description="Password (6-72 characters)"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        # Bcrypt has a 72-byte limit, but we limit to 72 characters
        # which is sufficient for most use cases
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password too long (max 72 bytes)")
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== Mindmap Schemas =====

class MindmapBase(BaseModel):
    title: str
    content: str

class MindmapCreate(MindmapBase):
    pass

class MindmapUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class MindmapResponse(MindmapBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ===== Token Schemas =====

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ===== Admin Stats Schemas =====

class AdminStats(BaseModel):
    total_users: int
    total_mindmaps: int
    active_users: int
    admin_count: int
