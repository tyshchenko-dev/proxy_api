import os
import shutil
import time
import logging
import subprocess

class OpenVPNStartError(Exception):
    pass

class WaitIPError(Exception):
    pass

class FindIPError(Exception):
    pass

class OpenVPNManager:
    def __init__(self, config):
        self.config = config

    def prepare_ovpn_config(self, folder_name: str, file_name: str, tunnel: str) -> str:
        config_text = self.config.OVPN_CONFIG_TEMPLATE.replace('{{adapter_name}}', tunnel)

        logging.info(f"Copy config file to {self.config.TEMP_FOLDER}")
        config_full_path = os.path.join(self.config.CONFIGS_FOLDER, folder_name, file_name)
        shutil.copy(config_full_path, self.config.TEMP_FOLDER)
        ovpn_temp_path = os.path.join(self.config.TEMP_FOLDER, file_name)
        logging.info(f"Append ovpn config to {ovpn_temp_path}")
        with open(ovpn_temp_path, 'a') as f:
            f.write(config_text)

        return ovpn_temp_path

    def start_openvpn(self, config_path: str):
        try:
            process = subprocess.Popen([
                "sudo",
                "openvpn",
                "--config",
                config_path,
                "--daemon"
            ])
            return process.pid
        except Exception as e:
            raise OpenVPNStartError("Failed to start OpenVPN") from e

    def wait_for_vpn_ip(self, tunnel: str, ovpn_temp_path: str, max_attempts: int = 10):
        for attempt in range(1, max_attempts + 1):
            logging.info(f"Try {attempt}/{max_attempts}: try to find adapter {tunnel} ip")
            try:
              vpn_ip = self.get_vpn_ip(tunnel)
              
              if vpn_ip:
                logging.info(f"IP found: {vpn_ip}")
                return vpn_ip
              else:
                logging.info("IP not found, sleep 1 second...")
                time.sleep(1)
            except Exception as e:
              logging.info(f"Can't find ip: {str(e)}")
              time.sleep(1)
        else:
            os.remove(ovpn_temp_path)
            raise WaitIPError(f"Can't find adapter ip: {tunnel}")

    def get_vpn_ip(self, tunnel: str):
        try:
            output = subprocess.check_output(['ip', '-4', 'addr', 'show', 'dev', tunnel]).decode()
            for line in output.splitlines():
                if 'inet ' in line:
                    return line.strip().split()[1].split('/')[0]
        except Exception as e:
            raise FindIPError(f"Failed to get IP from {tunnel}: {e}")
