from pydantic import BaseModel, EmailStr

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    username: str
    role: str

class SeedAdminIn(BaseModel):
    username: str
    password: str
    role: str = "admin"
