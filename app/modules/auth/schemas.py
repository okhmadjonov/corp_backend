from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _bcrypt_limit(value: str) -> str:
    # bcrypt 72 BAYTdan uzun parolni qabul qilmaydi (ʻ, ў kabi harflar 2-3 bayt)
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Parol juda uzun (72 baytdan oshmasin)")
    return value


Password = Annotated[str, Field(min_length=6, max_length=72), AfterValidator(_bcrypt_limit)]


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=100)
    password: Password
    full_name: str = Field(min_length=2, max_length=150)


class LoginRequest(BaseModel):
    login: str
    password: str


class TokenResponse(BaseModel):
    """Refresh token javobda emas — u httpOnly cookie'da keladi."""
    access_token: str
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