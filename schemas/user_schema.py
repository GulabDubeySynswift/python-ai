from pydantic import BaseModel

class UserLogin(BaseModel):
    email: str
    password: str
    
class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True