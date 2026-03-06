from sqlalchemy import Column, Integer, String, Boolean, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())

class MindMap(Base):
    __tablename__ = "mindmaps"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    user = relationship("User", backref="mindmaps")
    nodes = relationship("Node", back_populates="mindmap", cascade="all, delete-orphan")

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    mindmap_id = Column(Integer, ForeignKey("mindmaps.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    x_pos = Column(Float, default=0.0, nullable=False)
    y_pos = Column(Float, default=0.0, nullable=False)
    style_json = Column(Text)  # JSON string for custom styling
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    
    mindmap = relationship("MindMap", back_populates="nodes")
    parent = relationship("Node", remote_side=[id])
