import platform
import secrets
import shutil
import os
import subprocess
import venv
import string

import dotenv

CONF_NAME = "lazy_game_servers.conf"

MANUAL_INSTALL_INFO = """
Any values wrapped with ${} in the config are replaced with a value by the installer.
When manually installing, you will need to substitute the appropriate values yourself.
Any double dollar signs ($$) should also be replaced by a single dollar sign.
"""

_cmd_installed_cache = {}
def cmd_installed(cmd):
    if cmd not in _cmd_installed_cache:
        _cmd_installed_cache[cmd] = shutil.which(cmd) is not None
    return _cmd_installed_cache[cmd]

def copy_with_replacements(input_filename, output_filename, replacements):
    with open(input_filename, "r") as input_file:
        input_file_contents = input_file.readlines()
    output_file_contents = []
    for line in input_file_contents:
        template = string.Template(line)
        output_file_contents.append(template.substitute(replacements))
    with open(output_filename, "w") as output_file:
        output_file.writelines(output_file_contents)

if platform.system() == "Windows":
    print("Installer not available on Windows yet!")
    print("Try installing on Linux instead!")
    exit(-1)

# map of dependency commands to whether or not they are required
DEPENDENCIES = {
    "nginx": False,
    "supervisord": False,
    "npm": True
}

for dependecy, required in DEPENDENCIES.items():
    if not cmd_installed(dependecy):
        print(f"Dependecy \"{dependecy}\" was not found!")
        if required:
            print("Please make sure it is installed and available on PATH and try again")
            exit(-1)
        else:
            print("We will skip the part of the installer that requires it!")

EXTERNAL_PORT = 80
INTERNAL_PORT = 8000

FRONTEND_ASSETS_PATH = "/var/www/html/lazy_game_servers"

CONFIG_REPLACABLE = {
    "CWD": os.getcwd(),
    "EXTERNAL_PORT": EXTERNAL_PORT,
    "INTERNAL_PORT": INTERNAL_PORT,
    "FRONTEND_ASSETS_PATH": FRONTEND_ASSETS_PATH,
}

if not os.path.exists("venv"):
    print("Creating venv...")
    # symlinks should be False on Windows, but this script doesn't run on Windows so it's just hardcoded
    venv.create("venv", symlinks=True, with_pip=True)

print("Installing dependecies...")
subprocess.run(["venv/bin/pip", "install", "-r", "requirements.txt"])


print("Settings up .env file...")
if dotenv.get_key(".env", "LGS_TOKEN_SECRET") is None:
    dotenv.set_key(".env", "LGS_TOKEN_SECRET", secrets.token_hex(64))


print("Building frontend...")

NPM_DIR = "app/webapp/frontend"

subprocess.run(["npm", "install"], cwd=NPM_DIR)
npm_build = subprocess.run(["npm", "run", "build"], cwd=NPM_DIR)
if npm_build.returncode != 0:
    print("Non zero return code from running \"npm run build\"!")
    exit(-1)

if os.path.exists(FRONTEND_ASSETS_PATH):
    print("Old frontend build found, removing...")
    shutil.rmtree(FRONTEND_ASSETS_PATH)
print("Moving frontend build to", FRONTEND_ASSETS_PATH)
shutil.move("app/webapp/frontend/build", FRONTEND_ASSETS_PATH)

NGINX_SITES_AVAILABLE = '/etc/nginx/sites-available'
NGINX_SITES_ENABLED = '/etc/nginx/sites-enabled'

NGINX_CONF_NAME = CONF_NAME

if cmd_installed("nginx"):
    if os.path.exists(NGINX_SITES_AVAILABLE) and os.path.exists(NGINX_SITES_ENABLED):
        print("Found nginx sites-available and sites-enabled directories, auto installing and enabling nginx config")

        if os.path.exists(NGINX_SITES_ENABLED + "/default"):
            print("WARNING: default nginx conf is still enabled!")
            print("You may need to remove this if you are using the default port,")
            print("  and probably will want to remove it anyway")
        
        abs_conf_path = NGINX_SITES_AVAILABLE + "/" + NGINX_CONF_NAME

        copy_with_replacements("default_configs/nginx.conf", abs_conf_path, CONFIG_REPLACABLE)

        enabled_path = NGINX_SITES_ENABLED + "/" + NGINX_CONF_NAME
        if not os.path.exists(enabled_path):
            os.symlink(abs_conf_path, enabled_path)

        subprocess.run(["nginx", "-s", "reload"])

        print("Successfully added and enabled nginx config")
    else:
        print("No supported nginx config found!")
        print("Please manually install the config found in default_configs/nginx.conf")
        print(MANUAL_INSTALL_INFO)

SUPERVISOR_CONF_D = "/etc/supervisor/conf.d"
SUPERVISOR_CONF_NAME = CONF_NAME

if cmd_installed("supervisord"):
    if os.path.exists(SUPERVISOR_CONF_D):
        print("Found supervisor conf.d directory, auto installing supervisor config")

        copy_with_replacements("default_configs/supervisor.conf", SUPERVISOR_CONF_D + "/" + SUPERVISOR_CONF_NAME, CONFIG_REPLACABLE)

        subprocess.run(["supervisorctl", "reload"])
    else:
        print("No supported supervisor config found!")
        print("Please manually install the config found in default_configs/supervisor.conf")
        print(MANUAL_INSTALL_INFO)

print("Finished setup!")
