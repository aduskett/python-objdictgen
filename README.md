# Objdictgen

This is the objdicgen and objdictedit tool for working with OD-files used
on the CANOpen/CanFestival communication stack used in Levo CAN Modules.

This repo is a fork and extract of the upstream repo found at:

  * https://bitbucket.org/laerdalmedical/mirror-canfestival-3-asc


## Install

To run the `objdictedit` GUI, wxPython is required and it is only available
for Python 2.7. Download and install both.

   * https://www.python.org/downloads/release/python-2716/
   * https://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/

To setup the virtual environment run:

    $ py -2 -mvirtualenv --system-site-packages venv
    $ venv/Scripts/python -mpip install --upgrade pip wheel setuptools
    $ venv/Scripts/pip install .

NOTE: `py` is for Windows, and it requires python 3 to be installed on the
system.


## Python 3

`objdictgen` supports Python3. To install into a virtual enviornement `venv`.
Check out this repo and go to the top in a command-prompt (here assuming
git bash):

    $ py -3 -mvenv venv
    $ venv/Scripts/python -mpip install --upgrade pip wheel setuptools
    $ venv/Scripts/pip install .

After this `venv/Scripts/objdictgen.exe` will exist and can be called
from anywhere to run it.
