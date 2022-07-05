# Objdictgen

This is the objdicgen and objdictedit tool for working with OD-files used
on the CANOpen/CanFestival communication stack used in Levo CAN Modules.

This repo is a fork and extract of the upstream repo found at:

  * https://bitbucket.org/laerdalmedical/mirror-canfestival-3-asc


## Motivation

The biggest improvement with the new tool is the introduction of a new `.json`
based format to store the object dictionary. This format is well-known and easy
to read. It supports C-like comments in the json file. `odg` will process the
file in a repeatable manner, making it possible support diffing of the `.json`
file output. `odg` remains 100% compatible with the legacy `.od` format on both
input and output.


## Install

To install into a virtual enviornement `venv`. Check out this repo and go to
the top in a command-prompt (here assuming git bash):

    $ py -3 -mvenv venv
    $ venv/Scripts/python -mpip install --upgrade pip wheel setuptools
    $ venv/Scripts/pip install .

After this `venv/Scripts/odg.exe` will exist and can be called
from anywhere to run it.


### Python 2

To run the `objdictedit` GUI, wxPython is required and it is only available
for Python 2.7. Download and install both.

   * https://www.python.org/downloads/release/python-2716/
   * https://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/

To setup the virtual environment run (assuming git bash):

    $ py.exe -2 -mvirtualenv --system-site-packages venv
    $ venv/Scripts/python -mpip install --upgrade pip wheel setuptools
    $ venv/Scripts/pip install .

NOTE: The `py.exe` tools comes with Python 3.
