#!/usr/bin/python
# just a small script to make working the project icon is easier,
# like exporting the svg to different sizes, packing sizes into a favicon,
# and copying the files to the public folder of the react project

# TODO avoid having two copies of the same icon file in two places

import os
import shutil
import sys

# these are the sizes that will be included in the favicon
favicon_sizes = [16, 32, 64]
# these are other sizes that will be copied as pngs to the public folder
other_sizes = [192, 512]

print("NOTE: Make sure both Inkscape and ImageMagick are on path!")

# quick and dirty check to see if we're in the icon folder.
# if not, we assume we're in the project root and try to cd
if not os.getcwd().endswith("icon"):
    os.chdir(os.path.join("app", "webapp", "frontend", "icon"))

def print_usage():
    print("usage: python icon_helper.py [generate] [pack] [copy]")

if len(sys.argv) > 1:
    args = sys.argv
else:
    print_usage()
    args = input("input args: ").split(' ')

vaild_cmd = False

def get_filename(size, ext = "png"):
    return f"icon{size}.{ext}"

force = '--force' in args

if "generate" in args:
    valid_cmd = True
    sizes = favicon_sizes + other_sizes
    print("generating sizes:", ' '.join([str(size) for size in sizes]))
    for size in sizes:
        filename = get_filename(size)
        if os.path.exists(filename):
            if force:
                print(f"--force was passed, overwriting {filename}")
            else:
                print(f"file {filename} already exists, skipping")
                continue
        os.system(f"inkscape --export-background-opacity=0 --export-height={size} --export-type=png --export-filename=\"{filename}\" icon.svg")
if "pack" in args:
    valid_cmd = True
    os.system(f"magick " + ' '.join([get_filename(size) for size in favicon_sizes]) + " favicon.ico")
if "copy" in args:
    valid_cmd = True
    path = os.path.join("..", "public") 
    shutil.copy("favicon.ico", path)
    for size in other_sizes:
        shutil.copy(get_filename(size), path)

if not valid_cmd:
    print_usage()
