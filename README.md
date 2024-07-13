# Lazy Game Servers
A new Game Server Manager aimed to conserve disk space by sharing files between servers,
and to provide rich integrations with the game server.


## Features
> ⚠️ WARNING! ⚠️
> 
> THIS PROJECT IS STILL UNDER DEVELOPMENT!
>
> Not all features listed here may actually be complete!
> They will all be added at some point.

### File Sharing
Each game has a central storage location where any files can be stored.
These can be shared using symlinks to avoid having multiple copies of a game binary, or copied just to provide default configuration files that are still different per server.

### Game Intergration
Each server type has features tailored to their specific game, allowing for easier management.
For example, Minecraft will have a way to view online players, and ban or OP them directly in the GUI.
For servers that don't provide a default way to get more detailed information, you will need to use a mod to provide it to a manager plugin.

### Extensibility
Adding custom games is done with a Python script, so you have complete control over how the game is added.
You can also provide custom pages to the frontend to show extra game details and settings in anyway you see fit.


## Setup

### Development
Just clone the repo and open in VS Code, there are tasks and debug configurations already setup.

### Deployment

<!-- Through trial and error I found 3.10 is the minimum version of Python needed,
but I don't know what version of npm is needed. -->
* Requires at least Python 3.10 to run the backend, and npm 10.2.5 to compile the frontend.

* Requires a reverse proxy to serve the backend API and frontend on the same address, and optionally a program to autostart the API on boot.
    * The install script detects Ubuntu-like nginx and supervisor configs (`sites-available/` and `sites-enabled/` in `/etc/nginx/` and `conf.d/` in `/etc/supervisor/`)
    and will automatically install files to these directories.

After cloning the repo, just run `install.py` with sudo and it will automatically deploy to any supported configs.

If you don't have a supported config, you can manually deploy using these steps:
1. Setup virtual envrionment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Build frontend
```bash
cd app/webapp/frontend
npm install
npm build
```
3. Configure your reverse proxy/process manager.

    The backend can be started by running `venv/bin/python3 main.py` with this directory as the current working directory.
    `main.py` also takes some arguments, `--port` specifies what port it should be run on, and `--directory` specifies what directory files should be stored in.

    Any requests to `/api` should be proxied to the backend, otherwise just serve the frontend (all routing is done client side)
