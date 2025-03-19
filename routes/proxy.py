from fastapi import APIRouter, Path, HTTPException, Depends, status, Request
import logging
import re
import os
import time
import shutil
import json


import config

from auth.authenticate import authenticate

from models.proxy import LocaleItems, ProxyItems, StartRequest, ConfigItems

proxy_router = APIRouter()

@proxy_router.get("/locales/", response_model=LocaleItems, summary="List all available locales")
async def list_all_countries(request: Request, user:str=Depends(authenticate)) -> dict:
    return request.app.state.proxy_service.list_locales()

@proxy_router.get("/configs/{country}", response_model=ConfigItems, summary="Get proxies by country")
async def get_country_proxies(request:Request, country: str = Path(..., title="Name of country"), user: str = Depends(authenticate)) -> dict:
    return request.app.state.proxy_service.show_proxies_by_country(country)
@proxy_router.get("/proxies/", response_model=ProxyItems)
async def list_active_proxies(request: Request, user:str=Depends(authenticate)) -> dict:
    return request.app.state.proxy_service.list_active_proxies()

@proxy_router.get("/stop/{tun}")
async def stop(request:Request, tun: str = Path(..., title="Name of adapter on a linux server"), user:str=Depends(authenticate)) -> dict:
    return request.app.state.proxy_service.stop_proxy(tun)

@proxy_router.post("/start/")
async def start(start_request: StartRequest, request: Request, user: str = Depends(authenticate)) -> dict:
    return request.app.state.proxy_service.start_proxy(start_request)