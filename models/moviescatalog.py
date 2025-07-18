from pydantic import BaseModel, Field, field_validator
from typing import Optional

class MovieCatalog(BaseModel):
    movieId: Optional[int] = Field(
        default=None,
        ge=1,
    )

    title: str = Field(
        ...,
        min_length=1,
    )

    genres: Optional[str] = Field(
        default=None,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("El título no puede estar vacío o en blanco")
        return v

class MovieCreate(BaseModel):
    title: str = Field(..., min_length=1)
    genres: str = Field(..., min_length=1) 
