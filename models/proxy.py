from pydantic import BaseModel
from typing import List


class StartRequest(BaseModel):
    config_name: str
    folder_name: str
    

class LocaleItem(BaseModel):
    item: str

    class Config:
        json_schema_extra = {
            "example": {
                "item": "en"
            }
        }


class LocaleItems(BaseModel):
    locales: List[LocaleItem]

    class Config:
        json_schema_extra = {
            "example": {
                "locales": [
                    {"item": "en"},
                ]
            }
        }


class ProxyItem(BaseModel):
    proxy: List[str]
    ovpn_temp: str
    ip: str
    port: int
    adapter: str
    login: str
    password: str
    ignore_path: str
    location_code: str
    ping: int

    class Config:
        json_schema_extra = {
            "example": {
                "proxy": "socks5://127.0.0.1:1080",
                "ovpn_temp": "C:\\Users\\baggins\\Desktop\\vpn_proxy_api\\ovpn_temp\\be.ovpn",
                "ip": "127.0.0.1",
                "port": 1080,
                "adapter": "tun1",
                "login": "admin",
                "password": "<PASSWORD>",
                "ignore_path": "C:\\Users\\baggins\\Desktop\\vpn_proxy_api\\ovpn_temp\\be.ovpn",
                "location_code": "uk",
                "country": "United Kingdom",
                "ping": 0
            }
        }


class ProxyItems(BaseModel):
    proxies: List[ProxyItem]

    class Config:
        json_schema_extra = {
            "example": {
                "proxies": [
                    {
                        "proxy": "socks5://127.0.0.1:1080",
                        "ovpn_temp": "C:\\Users\\baggins\\Desktop\\vpn_proxy_api\\ovpn_temp\\be.ovpn",
                        "ip": "127.0.0.1",
                        "port": 1080,
                        "adapter": "tun1",
                        "login": "admin",
                        "password": "<PASSWORD>",
                        "ignore_path": "C:\\Users\\baggins\\Desktop\\vpn_proxy_api\\ovpn_temp\\be.ovpn",
                        "location_code": "uk",
                        "country": "United Kingdom",
                        "ping": 0
                    }
                ]
            }
        }


class ConfigItem(BaseModel):
    item: str

    class Config:
        json_schema_extra = {
            "example": {
                "item": "al-31.protonvpn.udp.ovpn",
            }
        }

class ConfigItems(BaseModel):
    items: List[ConfigItem]
    class Config:
        json_schema_extra = {
            "example": {
                "items": ["al-31.protonvpn.udp.ovpn", "af-1.protonvpn.udp.ovpn"],
            }
        }