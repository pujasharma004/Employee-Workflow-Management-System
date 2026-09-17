from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RequestCreate(BaseModel):
    title:str
    description:str
    category:str
    priority:str="Medium"
    user_id: int

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "employee"

class DepartmentCreate(BaseModel):
    name: str

class RequestResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    user_id: int | None = None
    department_id: int | None = None
    sla_deadline: datetime | None = None

    class Config:
        from_attributes = True