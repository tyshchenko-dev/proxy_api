from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from typing import Optional


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    

class LoginData(BaseModel):
    username: str
    password: str