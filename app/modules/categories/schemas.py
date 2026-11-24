from pydantic import BaseModel, ConfigDict, Field


class NameIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=50)


class NameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TagOut(NameOut):
    slug: str