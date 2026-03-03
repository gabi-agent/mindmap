from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import os

from database import get_db, User, Mindmap, engine, Base
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    MindmapCreate, MindmapUpdate, MindmapResponse,
    AdminStats
)
from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_active_user, get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="MindMap API",
    description="MindMap Application with Markmap Integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/app")
async def serve_frontend():
    return FileResponse('static/index.html')

# Redirect root to app
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "mindmap-api"}

# ===== Root Endpoint =====

@app.get("/")
async def root():
    return FileResponse('static/index.html')

@app.get("/api")
async def api_root():
    return {"message": "MindMap API v1.0", "docs": "/docs", "frontend": "/app"}

# ===== Auth Routes =====

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT token"""
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user

# ===== Mindmap Routes =====

@app.get("/api/mindmaps", response_model=List[MindmapResponse])
async def list_mindmaps(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all mindmaps of current user"""
    mindmaps = db.query(Mindmap).filter(Mindmap.user_id == current_user.id).all()
    return mindmaps

@app.post("/api/mindmaps", response_model=MindmapResponse, status_code=status.HTTP_201_CREATED)
async def create_mindmap(
    mindmap: MindmapCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new mindmap"""
    db_mindmap = Mindmap(
        title=mindmap.title,
        content=mindmap.content,
        user_id=current_user.id
    )
    db.add(db_mindmap)
    db.commit()
    db.refresh(db_mindmap)
    return db_mindmap

@app.get("/api/mindmaps/{mindmap_id}", response_model=MindmapResponse)
async def get_mindmap(
    mindmap_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific mindmap"""
    mindmap = db.query(Mindmap).filter(
        Mindmap.id == mindmap_id,
        Mindmap.user_id == current_user.id
    ).first()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    
    return mindmap

@app.put("/api/mindmaps/{mindmap_id}", response_model=MindmapResponse)
async def update_mindmap(
    mindmap_id: int,
    mindmap_update: MindmapUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a mindmap"""
    mindmap = db.query(Mindmap).filter(
        Mindmap.id == mindmap_id,
        Mindmap.user_id == current_user.id
    ).first()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    
    # Update fields
    if mindmap_update.title is not None:
        mindmap.title = mindmap_update.title
    if mindmap_update.content is not None:
        mindmap.content = mindmap_update.content
    
    db.commit()
    db.refresh(mindmap)
    return mindmap

@app.delete("/api/mindmaps/{mindmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mindmap(
    mindmap_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a mindmap"""
    mindmap = db.query(Mindmap).filter(
        Mindmap.id == mindmap_id,
        Mindmap.user_id == current_user.id
    ).first()
    
    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")
    
    db.delete(mindmap)
    db.commit()
    return None

# ===== Admin Routes =====

@app.get("/api/admin/stats", response_model=AdminStats)
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""
    total_users = db.query(User).count()
    total_mindmaps = db.query(Mindmap).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_count = db.query(User).filter(User.is_admin == True).count()
    
    return AdminStats(
        total_users=total_users,
        total_mindmaps=total_mindmaps,
        active_users=active_users,
        admin_count=admin_count
    )

@app.get("/api/admin/users", response_model=List[UserResponse])
async def list_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return users

@app.get("/api/admin/mindmaps", response_model=List[MindmapResponse])
async def list_all_mindmaps(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all mindmaps (admin only)"""
    mindmaps = db.query(Mindmap).all()
    return mindmaps

# ===== Run Application =====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
