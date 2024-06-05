# Icon

These are some notes about how icons are handled in this project.

## Files
`icon.svg` is the master icon, changes to the design itself should happen there.

`icon<size>.png` is the icon scaled to that size.
These are rendered from the master SVG, then manually tweaked because rendering from the SVG doesn't produce good results at smaller sizes.

`favicon.ico` is just a favicon containing the smaller sizes.

`icon_helper.py` is a Python helper script to make working with these files easier, see below.

Currently there are two copies of most files: one in this `icon` directory, and another in the `public` folder so that it is included in the React build.
I'm not sure how to eliminate these duplicates, or how big of a deal it is.
Maybe I can use symlinks? I don't know how git handles those... Problem for future me I guess.

## Helper Script

The helper script needs to run from the icon directory, however it can also be run in the project root since that is most IDEs default setting.

The script takes three parameters. If none are specified it will prompt for them, again for convenience when running in an IDE.
These parameters can be specified at the same time to run all of them, in this order:
* `generate`: Generates PNGs at each size for the favicon, and also some other sizes used outside of it.
If `--force` is used anywhere inside the command it will overwrite existing files
* `pack`: Takes the smaller PNGs and puts them into the favicon. Only works if the PNGs are already generated.
* `copy`: Copies the favicon and PNGs at any size not included in the favicon to the `public` folder. Should be done after after change so that you don't forget to do it later.

If other sizes are needed, change the lists at the top of the file so that the new size can be regenerated or copied as need.