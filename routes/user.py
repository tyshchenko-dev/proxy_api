from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from auth.jwt_handler import create_jwt_token

from models.user import User, TokenResponse, LoginData

from sqlmodel import select

from auth.hash_password import HashPassword

from database.connection import get_session

user_router = APIRouter(
    tags=["User"]
)

hash_password = HashPassword()

# @user_router.post("/signup", response_model=User)
# async def signup(data: User, session=Depends(get_session)) -> User:
#    user = session.exec(select(User).where(User.username == data.username)).first()
#    if user:
#        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
#
#    hashed_password = hash_password.create_hash(data.password)
#    data.password = hashed_password
#    session.add(data)
#    session.commit()
#    session.refresh(data)
#
#    return data


@user_router.post("/signin")
async def signin(user: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)) -> dict:
    user_in = session.exec(select(User).where(User.username == user.username)).first()
    if user_in is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if hash_password.verify_hash(user.password, user_in.password):
        access_token = create_jwt_token(user_in.username)
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="jwt_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="strict"
        )

        return response
        # return {
        #     "access_token": access_token,
        #     "token_type": "Bearer",
        # }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

@user_router.post("/v2/signin")
async def signin(data: LoginData, session=Depends(get_session)) -> dict:
    user_in = session.exec(select(User).where(User.username == data.username)).first()
    if user_in is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if hash_password.verify_hash(data.password, user_in.password):
        access_token = create_jwt_token(user_in.username)
        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect password"
    )
