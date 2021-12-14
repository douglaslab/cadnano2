# Cadnano2 DNA Origami Design Software

## Overview
[Cadnano](http://cadnano.org/) is computer-aided design software for DNA origami nanostructures. The original citation is [here](https://academic.oup.com/nar/article/37/15/5001/2409858).

## Installation

**OS X**
* Install [homebrew](https://brew.sh/)
* Install python3: `brew install python3`
* Create a virtualenv: `python3 -m venv ~/virtualenvs/cn24x` 
* Activate virtualenv:  `source ~/virtualenvs/cn24x/bin/activate`
* Install via pip: `pip3 install cadnano2`

**Windows**
* Download and install latest [python3](https://www.python.org/downloads/)
* `pip3 install cadnano2`

**Linux**
* Create a virtual env: `python3 -m venv ~/virtualenvs/cn24x`
* Activate the venv: `source ~/virtualenvs/cn24x/bin/activate`
* Install from PyPI: `pip3 install cadnano2`

## Running
* Open the Terminal
* Activate virtual env: `source ~/virtualenvs/cn24x/bin/activate`
* Run the app: `cadnano2`

## Development

**Build new dist and upload to PyPi**

* `pip install build` <- install [build](https://pypi.org/project/build/)
* `cd /path/to/cadnano2/` 
* `python3 -m build`  creates dist/cadnano2-x.y.z.tar.gz and cadnano2-x.y.z-py3-none-any.whl
* `python3 -m twine upload dist/cadnano2-x.y.z*` 

## Version notes

This version of Cadnano2 is maintained by the [Douglas Lab](http://bionano.ucsf.edu/). It is derived from [cadnano/cadnano2](https://github.com/cadnano/cadnano2).

If you wish to use the Cadnano Python API for scripting, see [cadnano2.5](https://github.com/douglaslab/cadnano2.5/).

## License

This version of Cadnano2 is available under the MIT License. GUI code that uses PyQt6 is GPLv3 as [required](http://pyqt.sourceforge.net/Docs/PyQt6/introduction.html#license) by Riverbank Computing.
