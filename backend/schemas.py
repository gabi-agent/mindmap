from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- MindMap Schemas ---
class MindMapBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_public: bool = False

class MindMapCreate(MindMapBase):
    pass

class MindMapUpdate(MindMapBase):
    pass

class MindMapResponse(MindMapBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    node_count: Optional[int] = 0

class MindMapListResponse(BaseModel):
    mindmaps: List[MindMapResponse]
    total: int
    page: int
    limit: int

# --- Node Schemas ---
class NodeStyle(BaseModel):
    border_color: Optional[str] = "#3b82f6"
    border_width: Optional[int] = 1
    border_style: Optional[str] = "solid"  # solid, dashed, dotted
    background_color: Optional[str] = "#ffffff"
    text_color: Optional[str] = "#000000"
    font_size: Optional[int] = 14
    font_weight: Optional[str] = "normal"  # normal, bold
    border_radius: Optional[int] = 8
    padding: Optional[int] = 10

class NodeBase(BaseModel):
    content: str = Field(..., min_length=1)
    x_pos: float = Field(default=0.0, ge=-10000, le=10000)
    y_pos: float = Field(default=0.0, ge=-10000, le=10000)
    style: Optional[NodeStyle] = None

class NodeCreate(NodeBase):
    parent_id: Optional[int] = None
    mindmap_id: int  # Not in schema, comes from path

class NodeUpdate(NodeBase):
    parent_id: Optional[int] = None

class NodeBatchItem(NodeUpdate):
    id: int

class NodeResponse(NodeBase):
    id: int
    mindmap_id: int
    parent_id: Optional[int]
    style_json: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class NodeBatchUpdate(BaseModel):
    nodes: List[NodeBatchItem]

# --- Pagination Schema ---
class PaginatedResponse(BaseModel):
    page: int = 1
    limit: int = 20
