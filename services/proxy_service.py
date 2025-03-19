import os
import re
import shutil
import logging
import time
from fastapi import HTTPException, status
import copy

from utils.route_utils import create_route, delete_route, create_rule, delete_rule
from utils.command_utils import start_3proxy, find_ovpn_pid, find_3proxy_pid, kill_process, init_proxy_cfg, get_directory_files_json, init_proxies_from_cache

from managers.openvpn_manager import OpenVPNManager, OpenVPNStartError, FindIPError, WaitIPError
from managers.proxy_manager import ProxyManager, TunnelNotFoundError, CountryConfigsNotFoundError, LocalesNotFoundError


class ProxyService:
    def __init__(self, config):
        self.config = config
        config.setup_logging()
        self.openvpn_manager = OpenVPNManager(config)
        self.proxy_manager = ProxyManager(config)
        init_proxy_cfg(config)

        # try init proxy from state file after reload or error
        proxy_state = init_proxies_from_cache()

        if proxy_state is not None:
            logging.info("Try init proxy service from proxy state file")
            self.proxy_manager.active_proxies = copy.deepcopy(proxy_state)
            del proxy_state
            logging.info(self.proxy_manager.active_proxies)
            for key, values in self.proxy_manager.active_proxies.items():
                if not values:
                  continue
                vpn_ip = values["vpn_ip"]
                current_port = values["port"]
                logging.info(f"Append proxy to proxy.cfg file, vpn_ip: {vpn_ip}, current_port: {current_port}")
                self.proxy_manager.add_new_proxy(vpn_ip, current_port, "socks5")
                self.proxy_manager.add_new_proxy(vpn_ip, int(current_port) + 10, "http")

        cache_data = get_directory_files_json(config.CONFIGS_FOLDER)
        with open(config.CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache_data)

    def show_proxies_by_country(self, country):
        try:
            return self.proxy_manager.show_configs_proxies_by_country(country)
        except CountryConfigsNotFoundError as e:
            logging.error("Country configs not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=str(e))
        except Exception as e:
            logging.error("Unknown error")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def list_locales(self):
        try:
            return self.proxy_manager.list_locales()
        except LocalesNotFoundError as e:
            logging.error("Locales not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    def list_active_proxies(self):
        return self.proxy_manager.list_active_proxies()

    def stop_proxy(self, tunnel):
        if tunnel in self.proxy_manager.active_proxies:
            target_tun = self.proxy_manager.active_proxies[tunnel]
            ignore_path = target_tun["ignore_path"]
            folder_name = target_tun["country"]
            proxy = target_tun["proxy"]
            ovpn_temp = target_tun["ovpn_temp"]
            vpn_ip = target_tun["vpn_ip"]
            table = target_tun["table"]
            #proxy_type = target_tun["protocol"]
            ovpn_pid = find_ovpn_pid(ovpn_temp)
            proxy_pid = find_3proxy_pid(os.path.join(self.config.ROOT_FOLDER, "proxy.cfg"))
            logging.info(f"Kill ovpn process: {ovpn_pid}")
            kill_process(ovpn_pid)
            logging.info(f"Kill 3proxy process: {proxy_pid}")
            kill_process(proxy_pid)
            logging.info(f"Remove ovpn path from temp folder: {ovpn_temp}")
            os.remove(ovpn_temp)
            logging.info(f"Stop proxy {proxy}")
            current_port = target_tun["port"]
            http_port = int(current_port) + 10
            
            socks_pattern = rf"^socks\s+-p{current_port}\b.*$"
            second_pattern = rf"^(socks|proxy)\s+-p\d+.*$"
            
            http_pattern = rf"^proxy\s+-p{http_port}\b.*$"

            should_start_proxy = False

            logging.info(f"Delete route for: {vpn_ip} and table: {table}")
            delete_route(vpn_ip, tunnel, table)

            logging.info(f"Delete rule for: {vpn_ip} and table: {table}")
            delete_rule(vpn_ip, table)

            with open(self.config.PROXY_CFG_FILE, "r+", encoding="utf-8") as file:
                proxy_data = file.read()
                proxy_data = re.sub(socks_pattern, "", proxy_data, flags=re.MULTILINE)
                proxy_data = re.sub(http_pattern, "", proxy_data, flags=re.MULTILINE)
                proxy_data = re.sub(r'\n{2,}', '\n', proxy_data)

                file.seek(0)
                file.write(proxy_data)
                file.truncate()

            try:
                logging.info("Try to find another socks proxy")
                another_socks = re.search(second_pattern, proxy_data, flags=re.MULTILINE).group()
                if another_socks:
                    logging.info("Found another socks proxy")
                    should_start_proxy = True
            except AttributeError:
                logging.info("Can't find another socks proxy")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")

            self.proxy_manager.active_proxies[tunnel] = None
            if should_start_proxy:
                logging.info(f"Restart 3proxy with updated config")
                start_3proxy(self.config.PROXY_CFG_FILE)

            old_config_path = os.path.join(self.config.CONFIGS_FOLDER, folder_name)

            shutil.move(ignore_path, old_config_path)
            logging.info(f"Move ignored config to {old_config_path}")
            self.proxy_manager.save_proxy_data()
            return {"proxy": proxy}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Can't find tun {tunnel}")

    def start_proxy(self, request):
        try:
            file = request.config_name
            folder_name = request.folder_name
            # proxy_type = request.proxy_type
            logging.info(f"Try to find free tunnel for config file: {file}")
            free_tun = self.proxy_manager.find_free_proxy_tunnel()
            tunnel = free_tun["tun"]
            tunnel_index = free_tun["index"]

            if tunnel is None and tunnel_index is None:
                logging.info(f"All tunnel is busy, try to release old tunnel")
                oldest_tunnel = self.proxy_manager.get_oldest_tunnel()
                self.stop_proxy(oldest_tunnel)
                free_tun = self.proxy_manager.find_free_proxy_tunnel()
                tunnel = free_tun["tun"]
                tunnel_index = free_tun["index"]
                
            logging.info(f"Tunnel finded: {tunnel} tunnel index: {tunnel_index}")

            logging.info(f"Try kill old proxy process")
            self.proxy_manager.kill_proxy()

            logging.info(f"Prepare ovpn config: {tunnel}")
            ovpn_temp_path = self.openvpn_manager.prepare_ovpn_config(folder_name, file, tunnel)

            logging.info(f"Start OpenVPN config: {ovpn_temp_path}")
            self.openvpn_manager.start_openvpn(ovpn_temp_path)

            # Try Find OVPN IP
            vpn_ip = self.openvpn_manager.wait_for_vpn_ip(tunnel, ovpn_temp_path)

            logging.info(f"Create route for {vpn_ip} via {tunnel}")
            table = 100 + int(tunnel_index)  # set table
            create_route(vpn_ip, tunnel, table)

            logging.info(f"Create rule for {vpn_ip}")
            create_rule(vpn_ip, table)

            socks_port = int(self.config.PROXY_PORT) + int(tunnel_index)
            http_port = int(self.config.PROXY_PORT) + int(tunnel_index) + 10
            self.proxy_manager.add_new_proxy(vpn_ip, http_port, "proxy")
            self.proxy_manager.add_new_proxy(vpn_ip, socks_port, "socks")
            logging.info(f"New proxy added to config: {self.config.PROXY_CFG_FILE}")
            start_3proxy(self.config.PROXY_CFG_FILE)
            logging.info(f"Proxy started. Sleep 2 seconds.")
            time.sleep(2)
            socks_proxy = f"socks5://{self.config.PROXY_LOGIN}:{self.config.PROXY_PASS}@{self.config.SERVER_IP}:{socks_port}"
            http_proxy = f"http://{self.config.PROXY_LOGIN}:{self.config.PROXY_PASS}@{self.config.SERVER_IP}:{http_port}"
            config_full_path = os.path.join(self.config.CONFIGS_FOLDER, folder_name, file)
            shutil.move(config_full_path, self.config.IGNORE_FOLDER)
            logging.info(f"Move config file to {self.config.IGNORE_FOLDER}")
            ignore_path = os.path.join(self.config.IGNORE_FOLDER, file)
            match = re.search(self.config.CODE_PATTERN, file)

            if match:
                location_code = match.group().upper()
            else:
                location_code = None

            proxy_ping = self.proxy_manager.proxy_speed(socks_proxy)

            logging.info(f"Save new proxy to active proxy list")
            self.proxy_manager.append_proxy_data(tunnel, [socks_proxy, http_proxy], ovpn_temp_path, socks_port, ignore_path, vpn_ip, table, location_code, folder_name, proxy_ping)

            return {"message": self.proxy_manager.active_proxies[tunnel]}
        except TunnelNotFoundError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except (OpenVPNStartError, FindIPError, WaitIPError) as e:
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))