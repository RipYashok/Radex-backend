from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    fullName: str
    status: str
    email: str
    password: str
    images: Optional[List[str]] = None
    reports: Optional[List[str]] = None

class UserOut(UserCreate):
    id: int

    class Config:
        orm_mode = True