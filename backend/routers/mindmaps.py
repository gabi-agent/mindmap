from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session as DBSession
from typing import Optional

from .. import models, database
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api", tags=["mindmaps"])

def verify_mindmap_ownership(mindmap_id: int, user_id: int, db: DBSession):
    mindmap = db.query(models.MindMap).filter(models.MindMap.id == mindmap_id).first()
    if mindmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MindMap not found"
        )
    if mindmap.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own mindmaps"
        )
    return mindmap

@router.get("/mindmaps")
def get_mindmaps(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    # Import schemas lazily to avoid circular import issues
    from .. import schemas
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get mindmaps for user
    mindmaps_query = db.query(models.MindMap).filter(models.MindMap.user_id == user.id)
    
    # Count total
    total = mindmaps_query.count()
    
    # Apply pagination
    mindmaps = mindmaps_query.offset((page - 1) * limit).limit(limit).all()
    
    return schemas.MindMapListResponse(
        mindmaps=[
            schemas.MindMapResponse(
                id=m.id,
                user_id=m.user_id,
                title=m.title,
                description=m.description,
                is_public=m.is_public,
                created_at=m.created_at,
                updated_at=m.updated_at,
                node_count=len(m.nodes)
            )
            for m in mindmaps
        ],
        total=total,
        page=page,
        limit=limit
    )

@router.get("/mindmaps/{mindmap_id}")
def get_mindmap(
    mindmap_id: int,
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    # Import schemas lazily
    from .. import schemas
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    mindmap = verify_mindmap_ownership(mindmap_id, user.id, db)
    
    return schemas.MindMapResponse(
        id=mindmap.id,
        user_id=mindmap.user_id,
        title=mindmap.title,
        description=mindmap.description,
        is_public=mindmap.is_public,
        created_at=mindmap.created_at,
        updated_at=mindmap.updated_at,
        node_count=len(mindmap.nodes)
    )

@router.post("/mindmaps", status_code=status.HTTP_201_CREATED)
def create_mindmap(
    mindmap_data: dict,
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    # Import schemas lazily
    from .. import schemas
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Parse and validate the request data
    mindmap = schemas.MindMapCreate(**mindmap_data)
    
    db_mindmap = models.MindMap(
        title=mindmap.title,
        user_id=user.id,
        description=mindmap.description,
        is_public=mindmap.is_public
    )
    db.add(db_mindmap)
    db.commit()
    db.refresh(db_mindmap)
    
    return schemas.MindMapResponse(
        id=db_mindmap.id,
        user_id=db_mindmap.user_id,
        title=db_mindmap.title,
        description=db_mindmap.description,
        is_public=db_mindmap.is_public,
        created_at=db_mindmap.created_at,
        updated_at=db_mindmap.updated_at,
        node_count=0
    )

@router.put("/mindmaps/{mindmap_id}")
def update_mindmap(
    mindmap_id: int,
    mindmap_data: dict,
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    # Import schemas lazily
    from .. import schemas
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    db_mindmap = verify_mindmap_ownership(mindmap_id, user.id, db)
    
    # Parse and validate the request data
    mindmap = schemas.MindMapUpdate(**mindmap_data)
    
    # Update fields
    update_data = mindmap.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mindmap, key, value)
    
    db.commit()
    db.refresh(db_mindmap)
    
    return schemas.MindMapResponse(
        id=db_mindmap.id,
        user_id=db_mindmap.user_id,
        title=db_mindmap.title,
        description=db_mindmap.description,
        is_public=db_mindmap.is_public,
        created_at=db_mindmap.created_at,
        updated_at=db_mindmap.updated_at,
        node_count=len(db_mindmap.nodes)
    )

@router.delete("/mindmaps/{mindmap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mindmap(
    mindmap_id: int,
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    db_mindmap = verify_mindmap_ownership(mindmap_id, user.id, db)
    
    db.delete(db_mindmap)
    db.commit()
    
    return None
