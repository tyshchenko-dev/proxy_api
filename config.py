import os
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIGS_FOLDER = os.path.join(ROOT_FOLDER, 'vpn_configs')
TEMP_FOLDER = os.path.join(ROOT_FOLDER, 'temp')
IGNORE_FOLDER = os.path.join(ROOT_FOLDER, 'ignore')
TEMPLATES_DIR = os.path.join(ROOT_FOLDER, "templates")
CACHE_FILE = os.path.join(ROOT_FOLDER, 'cache.json')
STATE_FILE = os.path.join(ROOT_FOLDER, 'proxy_state.json')
PROXY_CFG_FILE = os.path.join(ROOT_FOLDER, "proxy.cfg")
CODE_PATTERN = r"\w{2}(?=\-)"


PROXY_LOGIN = os.getenv("PROXY_LOGIN")
PROXY_PASS = os.getenv("PROXY_PASS")
SERVER_IP = os.getenv("SERVER_IP")
PROXY_PORT = os.getenv("PROXY_PORT")
DATABASE_URL = f"sqlite:///./proxy.db"
JWT_SECRET_KEY = os.getenv("JWT_SECRET")

if not os.path.exists(TEMP_FOLDER):
    os.mkdir(TEMP_FOLDER)

if not os.path.exists(IGNORE_FOLDER):
    os.mkdir(IGNORE_FOLDER)

OVPN_CONFIG_TEMPLATE = """
auth-user-pass userpass.txt
dev {{adapter_name}}
route 0.0.0.0 192.0.0.0 net_gateway
route 64.0.0.0 192.0.0.0 net_gateway
route 128.0.0.0 192.0.0.0 net_gateway
route 192.0.0.0 192.0.0.0 net_gateway
"""


PROXY_CONFIG_TEMPLATE = """
daemon
nscache 65536
log /var/log/3proxy/3proxy.log
logformat "L%Y-%m-%d %H:%M:%S %N.%p %E %U %C:%c %R:%r %O %I %h %T"
rotate 7

auth strong

users {{proxy_login}}:CL:{{proxy_pass}}

allow {{proxy_login}}

"""

OPEN_PROXY_TEMPLATE = """
{{proxy_type}} -p{{proxy_port}} -i0.0.0.0 -e{{adapter_ip}}
"""


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        handlers=[logging.FileHandler("log.log"), logging.StreamHandler(sys.stdout)],
    )