"""Base data models"""
from pydantic import BaseModel as PydanticBaseModel
from datetime import datetime
from typing import Optional


class BaseModel(PydanticBaseModel):
    """Base model for all data models"""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
