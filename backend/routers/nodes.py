from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from .. import models, database
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api", tags=["nodes"])

def verify_node_access(node_id: int, user_id: int, db: DBSession):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found"
        )
    
    # Get mindmap to check ownership
    mindmap = db.query(models.MindMap).filter(models.MindMap.id == node.mindmap_id).first()
    if mindmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MindMap not found"
        )
    
    if mindmap.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access nodes in your own mindmaps"
        )
    
    return node

@router.get("/mindmaps/{mindmap_id}/nodes")
def get_nodes(
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
    
    # Verify mindmap ownership
    mindmap = db.query(models.MindMap).filter(
        models.MindMap.id == mindmap_id,
        models.MindMap.user_id == user.id
    ).first()
    
    if mindmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MindMap not found"
        )
    
    nodes = db.query(models.Node).filter(models.Node.mindmap_id == mindmap_id).all()
    
    return [
        schemas.NodeResponse(
            id=node.id,
            mindmap_id=node.mindmap_id,
            parent_id=node.parent_id,
            content=node.content,
            x_pos=node.x_pos,
            y_pos=node.y_pos,
            style_json=node.style_json,
            created_at=node.created_at,
            updated_at=node.updated_at
        )
        for node in nodes
    ]

@router.post("/mindmaps/{mindmap_id}/nodes", status_code=status.HTTP_201_CREATED)
def create_node(
    mindmap_id: int,
    node_data: dict,
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
    
    # Verify mindmap ownership
    mindmap = db.query(models.MindMap).filter(
        models.MindMap.id == mindmap_id,
        models.MindMap.user_id == user.id
    ).first()
    
    if mindmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MindMap not found"
        )
    
    # Parse and validate the request data
    # Add mindmap_id from path parameter
    node_data['mindmap_id'] = mindmap_id
    node = schemas.NodeCreate(**node_data)
    
    # Serialize style to JSON string
    style_json = None
    if node.style:
        style_json = node.style.json()
    
    db_node = models.Node(
        mindmap_id=mindmap_id,
        parent_id=node.parent_id,
        content=node.content,
        x_pos=node.x_pos,
        y_pos=node.y_pos,
        style_json=style_json
    )
    db.add(db_node)
    db.commit()
    db.refresh(db_node)
    
    return schemas.NodeResponse(
        id=db_node.id,
        mindmap_id=db_node.mindmap_id,
        parent_id=db_node.parent_id,
        content=db_node.content,
        x_pos=db_node.x_pos,
        y_pos=db_node.y_pos,
        style_json=db_node.style_json,
        created_at=db_node.created_at,
        updated_at=db_node.updated_at
    )

@router.put("/nodes/{node_id}")
def update_node(
    node_id: int,
    node_data: dict,
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
    
    db_node = verify_node_access(node_id, user.id, db)
    
    # Parse and validate the request data
    node = schemas.NodeUpdate(**node_data)
    
    # Update fields
    update_data = node.dict(exclude_unset=True)
    
    # Serialize style to JSON string
    if "style" in update_data and update_data["style"]:
        update_data["style_json"] = update_data["style"].json()
        del update_data["style"]
    
    for key, value in update_data.items():
        setattr(db_node, key, value)
    
    db.commit()
    db.refresh(db_node)
    
    return schemas.NodeResponse(
        id=db_node.id,
        mindmap_id=db_node.mindmap_id,
        parent_id=db_node.parent_id,
        content=db_node.content,
        x_pos=db_node.x_pos,
        y_pos=db_node.y_pos,
        style_json=db_node.style_json,
        created_at=db_node.created_at,
        updated_at=db_node.updated_at
    )

@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(
    node_id: int,
    user: models.User = Depends(get_current_user),
    db: DBSession = Depends(database.get_db)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    db_node = verify_node_access(node_id, user.id, db)
    
    db.delete(db_node)
    db.commit()
    
    return None

@router.post("/nodes/batch")
def batch_update_nodes(
    batch_data: dict,
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
    batch = schemas.NodeBatchUpdate(**batch_data)
    
    updated_nodes = []
    for node_update in batch.nodes:
        db_node = db.query(models.Node).filter(models.Node.id == node_update.id).first()
        if db_node is None:
            continue  # Skip if node not found
        
        # Verify ownership through mindmap
        mindmap = db.query(models.MindMap).filter(models.MindMap.id == db_node.mindmap_id).first()
        if mindmap and mindmap.user_id != user.id:
            continue  # Skip if not owned by user
        
        # Update fields
        update_data = node_update.dict(exclude_unset=True)
        
        # Serialize style to JSON string
        if "style" in update_data and update_data["style"]:
            update_data["style_json"] = update_data["style"].json()
            del update_data["style"]
        
        for key, value in update_data.items():
            setattr(db_node, key, value)
        
        updated_nodes.append(db_node)
    
    db.commit()
    
    return {"message": f"Updated {len(updated_nodes)} nodes successfully"}
