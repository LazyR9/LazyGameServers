# Lazy Game Servers
<!-- TODO I used future tense because I wrote this before any code,
          once I write code I need to come back and change this -->

A new Game Server Manager aimed to conserve disk space by sharing files between servers using symlinks,
and to provide rich integrations with the game server.

## Conserving Space

A server for a single game type will have a central storage folder for things like executables or plugins, and each instance can use a symlink these files. By default these files are versioned so that all servers won't automatically update if a newer binary is downloaded, though they can be configured to do so.

## Game Intergration

Each server will have features tailored to the specific game, allowing for easier management. For example, Minecraft will have a way to view online players, and ban or op them with the click of a button.

Some games may have little to no intergration, and might need to have specific mods or plugins installed to provide extra features. These will be easy to install for each game.

## Extensibility

Extra game intergration will be a breeze to add, with an easy to use API to add new tabs and settings to the web UI, and to provide stats and management tools.