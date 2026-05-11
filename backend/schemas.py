from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    sponsor_id: Optional[int] = None
    parent_id: Optional[int] = None
    position: Optional[str] = None

class UserLogin(BaseModel):
    name: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    sponsor_id: Optional[int] = None
    parent_id: Optional[int] = None
    position: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
