import os
import subprocess
import signal
import logging
import psutil
import re
import time
import json

import config


def get_directory_files_json(root_path):
    result = {}

    for current_dir, dirs, files in os.walk(root_path):
        dir_name = os.path.basename(current_dir)
        if files:
            result[dir_name] = files

    return json.dumps(result, indent=4, ensure_ascii=False)

def find_3proxy_pid(config_path):
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and "3proxy" in cmdline and config_path in cmdline:
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def find_ovpn_pid(config_path):
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline and "--config" in cmdline and config_path in cmdline:
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def get_all_file_paths(directory):
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths


def kill_process(pid):
    try:
        os.kill(pid, signal.SIGKILL)
        logging.info(f"Process with PID {pid} killed successfully.")
    except ProcessLookupError:
        logging.error(f"Process with PID {pid} not found.")
    except PermissionError:
        logging.error(f"Need more rights for PID kill {pid}.")
    except Exception as e:
        logging.error(f"Error PID {pid}: {e}")


def run_command(command):
    try:
        process = subprocess.Popen(command)
        print(f"Start started with PID: {process.pid}")
        return process.pid
    except Exception as e:
        print(f"Error {' '.join(command)}: {e}")
        return None


def start_3proxy(config_file):
    try:
        process = subprocess.Popen([
            "sudo",
            "3proxy",
            config_file
        ])
        return process.pid
    except Exception as e:
        logging.error(f"Error starting 3proxy: {e}")
        return None


def find_free_tun(config):
    for key, value in config.ACTIVE_PROXIES.items():
        if value is None:
            tun_index = re.search(r"tun(\d+)", key).group(1)
            return {"tun": key, "index": tun_index}
    raise Exception(f"Can't find free tun adapter")


def find_config(config_name, config):
    files = os.listdir(config.CONFIGS_FOLDER)

    if len(files) == 0:
        raise Exception(f"Config folder is empty")

    files = [file for file in files if file == config_name]

    if len(files) == 0:
        raise Exception(f"Config for {config_name} not found")

    file = files[0]

    return file


def kill_proxy(config):
    proxy_pid = find_3proxy_pid(config.PROXY_CFG_FILE)
    logging.info(f"Kill 3proxy process: {proxy_pid}")
    if proxy_pid:
        kill_process(proxy_pid)


def init_proxy_cfg(config):
    proxy_config = config.PROXY_CONFIG_TEMPLATE.replace(
        '{{proxy_login}}', config.PROXY_LOGIN).replace("{{proxy_pass}}", config.PROXY_PASS)

    with open(config.PROXY_CFG_FILE, "w", encoding="utf-8") as f:
        f.write(proxy_config)

def init_proxies_from_cache():
    state_data = None
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE, "r", encoding="utf-8") as f:
          file_content =  f.read()
          state_data = json.loads(file_content)
    return state_data

def add_new_proxy(config, vpn_ip, current_port):
    proxy_config = config.OPEN_PROXY_TEMPLATE.replace('{{adapter_ip}}', vpn_ip).replace('{{proxy_port}}', str(current_port))
    with open(config.PROXY_CFG_FILE, "a", encoding="utf-8") as file:
        file.write(proxy_config)
