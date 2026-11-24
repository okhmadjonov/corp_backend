from pydantic import BaseModel, ConfigDict, Field



class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=2, max_length=150)
    
class LoginRequest(BaseModel):
    login: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    full_name: str
    role: RoleOut