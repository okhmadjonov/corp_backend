from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.schemas import RoleOut

RoleName = Literal["super_admin", "operator", "user"]


class UserCreate(BaseModel):
    login: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=2, max_length=150)
    role: RoleName = "operator"


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    role: RoleName


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=72)


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    full_name: str
    role: RoleOut
    created_at: datetime