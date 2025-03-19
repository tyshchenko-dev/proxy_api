import time
from datetime import datetime

from fastapi import HTTPException, status
from jose import jwt, JWTError

import config

def create_jwt_token(user: str) -> str:
    payload = {
        "user": user,
        "expires": time.time() + 86400
    }

    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm="HS256")

    return token


def verify_access_token(token: str) -> dict:
    try:
        data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        expire = data.get("expires")

        if expire is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token supplied")
        if datetime.utcnow() > datetime.utcfromtimestamp(expire):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired")

        return data

    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
