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

Right now setting up for both end users and other developers isn't very easy right now,
because some necessary files aren't automatically generated.
Hopefully that changes soon!
