from pydantic import BaseModel, EmailStr  # EmailStr mantido para uso futuro
from app.core.security import UserRole


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    role: UserRole


class SeedAdminIn(BaseModel):
    username: str
    password: str
    role: UserRole = "admin"

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

