from fastapi import FastAPI, Request, HTTPException, status, Cookie
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from typing import Optional

import uvicorn

from database.connection import conn
from services.proxy_service import ProxyService

import config

from routes.user import user_router
from routes.proxy import proxy_router

from auth.jwt_handler import verify_access_token, create_jwt_token

# init app
app = FastAPI()
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def main_redirect():
    return RedirectResponse(url="/login")


@app.get("/robots.txt")
def serve_robots_txt():
    return FileResponse("static/robots.txt")


@app.get("/login")
def get_login_page(request: Request, jwt_token: Optional[str] = Cookie(None)):
    if jwt_token:
        try:
            verify_access_token(jwt_token)
            return RedirectResponse(url="/dashboard")
        except HTTPException:
            response = templates.TemplateResponse("login.html", {"request": request})
            response.delete_cookie("jwt_token")
            return response
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard/")
def dashboard(request: Request, jwt_token: Optional[str] = Cookie(None), jwt_query: Optional[str] = None):
    token = jwt_token or jwt_query

    if not token:
        return RedirectResponse(url="/login")

    data = verify_access_token(token)
    
    if not data:
        return RedirectResponse(url="/login")
        
 
    if jwt_query:
        token = create_jwt_token(data.get("user"))
    
    response = templates.TemplateResponse("dashboard.html", {
        "request": request,
        "data": data,
        "jwt_token": token
    })
 
 
    response.set_cookie(key="jwt_token", value=token, httponly=True, secure=False, samesite="strict")    


    return response
    


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("jwt_token")
    return response


app.include_router(user_router, prefix="/user")
app.include_router(proxy_router, prefix="/proxy")


@app.on_event("startup")
def on_startup():
    conn()
    app.state.proxy_service = ProxyService(config)


if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=3000)
    uvicorn.run(app, host="0.0.0.0", port=3000)
