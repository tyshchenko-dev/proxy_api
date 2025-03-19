import logging
import re
import psutil
import json
import os
import requests
import time

from utils.command_utils import kill_process
from utils.utils import unix_time_now

class TunnelNotFoundError(Exception):
    pass

class CountryConfigsNotFoundError(Exception):
    pass

class LocalesNotFoundError(Exception):
    pass

class ProxyManager:
    def __init__(self, config):
        logging.info("ProxyManager created!")
        self.config = config
        self.active_proxies = {
            "tun1": None,
            "tun2": None,
            "tun3": None,
            "tun4": None,
            "tun5": None,
            "tun6": None,
            "tun7": None,
            "tun8": None,
            "tun9": None,
            "tun10": None
        }
    
    def proxy_speed(self, proxy):
      proxies = {
        "http": proxy,
        "https": proxy,
      }
      
      try:
        start = time.time()
        response = requests.get("https://www.google.com", proxies=proxies, timeout=10)
        response.raise_for_status()
        end = time.time()
        response_time_ms = int((end - start) * 1000)
      except Exception as e:
        logging.info(f"Error: {e} Proxy: {proxy}")
        response_time_ms = 0
    
      return response_time_ms

    def get_oldest_tunnel(self):
        oldest_tunnel_key = min(
            self.active_proxies,
            key=lambda tunnel_name: self.active_proxies[tunnel_name]["created_at"]
        )
        return oldest_tunnel_key

    def show_configs_proxies_by_country(self, country):
        with open(self.config.CACHE_FILE, "r", encoding="utf-8") as f:
            json_data = f.read()
            cache_data = json.loads(json_data)

        active_configs = []

        for key, values in self.active_proxies.items():
            if values is None:
                continue
            ignore_path = values.get("ignore_path", None)
            if ignore_path is not None:
                file_name = os.path.basename(ignore_path)
                active_configs.append(file_name)

        configs_list = cache_data.get(country, None)
        configs_list = [{"item": item} for item in configs_list if item not in active_configs]

        if configs_list is None:
            raise CountryConfigsNotFoundError(f"Country {country} proxies not found...")

        return {"items": configs_list}

    def list_locales(self):
        locales = [
            {"item": d} for d in os.listdir(self.config.CONFIGS_FOLDER)
            if os.path.isdir(os.path.join(self.config.CONFIGS_FOLDER, d))
        ]
        if len(locales) == 0:
            raise LocalesNotFoundError(f"Locales not found...")
        return {"locales": locales}

    def list_active_proxies(self):
        proxies_list = []
        for key, value in self.active_proxies.items():
            if value:
                proxies_list.append(value)
        return {"proxies": proxies_list}

    def find_free_proxy_tunnel(self):
        for key, value in self.active_proxies.items():
            if value is None:
                tun_index = re.search(r"tun(\d+)", key).group(1)
                return {"tun": key, "index": tun_index}
        return {"tun": None, "index": None}

    def kill_proxy(self):
        proxy_pid = self.find_3proxy_pid(self.config.PROXY_CFG_FILE)
        logging.info(f"Kill 3proxy process: {proxy_pid}")
        if proxy_pid:
            kill_process(proxy_pid)


    def find_3proxy_pid(self, config_path):
        for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if cmdline and "3proxy" in cmdline and config_path in cmdline:
                    return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None

    def add_new_proxy(self, vpn_ip, current_port, proxy_type):  
        proxy_config = self.config.OPEN_PROXY_TEMPLATE.replace('{{adapter_ip}}', vpn_ip).replace('{{proxy_port}}',
                                                                                            str(current_port)).replace('{{proxy_type}}', proxy_type)
        with open(self.config.PROXY_CFG_FILE, "a", encoding="utf-8") as file:
            file.write(proxy_config)

    def append_proxy_data(self, tunnel, active_proxy, ovpn_temp_path, current_port, ignore_path, vpn_ip, table, location_code, folder_name, ping):
        self.active_proxies[tunnel] = {
            "proxy": active_proxy,
            "ovpn_temp": ovpn_temp_path,
            "ip": self.config.SERVER_IP,
            "port": current_port,
            "adapter": tunnel,
            "login": self.config.PROXY_LOGIN,
            "password": self.config.PROXY_PASS,
            "ignore_path": ignore_path,
            "vpn_ip": vpn_ip,
            "table": table,
            "location_code": location_code,
            "country": folder_name,
            "ping": ping,
            "created_at": unix_time_now()
        }

        self.save_proxy_data()

    def save_proxy_data(self):
        save_path  = os.path.join(self.config.ROOT_FOLDER, "proxy_state.json")

        logging.info(f"Saving proxy data to {save_path}")

        with open(save_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(self.active_proxies))
