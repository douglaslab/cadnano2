# Cadnano2 DNA Origami Design Software

## Overview
[Cadnano](http://cadnano.org/) is computer-aided design software for DNA origami nanostructures. The original citation is [here](https://academic.oup.com/nar/article/37/15/5001/2409858).

## Installation

**macOS**
* Install [homebrew](https://brew.sh/)
* Install python3: `brew install python3`
* Create a virtualenv: `python3 -m venv ~/virtualenvs/cn24x` 
* Activate virtualenv: `source ~/virtualenvs/cn24x/bin/activate`
* Install via pip: `pip3 install cadnano2`

**Windows** (not tested)
* Download and install latest [python3](https://www.python.org/downloads/)
* Create a virtualenv: `python -m venv c:\virtualenvs\cn24x` 
* Activate virtualenv: `c:\virtualenvs\cn24x\Scripts\activate.bat`
* Install via pip: `pip3 install cadnano2`

**Linux**
* Create a virtual env: `python3 -m venv ~/virtualenvs/cn24x`
* Activate the venv: `source ~/virtualenvs/cn24x/bin/activate`
* Install from PyPI: `pip3 install cadnano2`

## Running
* Open the Terminal
* Activate virtual env: 
  - `source ~/virtualenvs/cn24x/bin/activate` (macOS or Linux)
  - `c:\virtualenvs\cn24x\Scripts\activate.bat` (Windows)
* Run the app: `cadnano2`

**macOS alias**
* Add to `~/.zprofile`: `alias cn2="source ~/virtualenvs/cn24x/bin/activate && cadnano2"`
* Open new Terminal and run: `cn2`

## Upgrading
* Open the Terminal
* Activate virtual env: `source ~/virtualenvs/cn24x/bin/activate`
* Upgrade via pip: `pip install --upgrade cadnano2`


## Development

**Setup a dev environment**

* Create a virtualenv: `python3 -m venv ~/virtualenvs/cn24dev` 
* Activate virtualenv: `source ~/virtualenvs/cn24dev/bin/activate`
* Install PyQt6: `pip install pyqt6`
* Clone repo: `git clone git@github.com:douglaslab/cadnano2.git`
* Change directory: `cd cadnano2`
* Make desired code edits
* Build and install: `python setup.py install`
* Test: `cadnano2`
* Repeat previous 3 steps as needed

**Build new dist and upload to PyPi**

* `pip install build twine` <- install [build](https://pypi.org/project/build/) and [twine](https://pypi.org/project/twine/)
* `cd /path/to/cadnano2/` 
* `python3 -m build`  creates dist/cadnano2-x.y.z.tar.gz and cadnano2-x.y.z-py3-none-any.whl
* `python3 -m twine upload dist/cadnano2-x.y.z*` 

## Version notes

This version of Cadnano2 is maintained by the [Douglas Lab](http://bionano.ucsf.edu/). It is derived from [cadnano/cadnano2](https://github.com/cadnano/cadnano2).

If you wish to use the Cadnano Python API for scripting, see [cadnano2.5](https://github.com/douglaslab/cadnano2.5/).

## License

This version of Cadnano2 is available under the MIT License. GUI code that uses PyQt6 is GPLv3 as [required](http://pyqt.sourceforge.net/Docs/PyQt6/introduction.html#license) by Riverbank Computing.
