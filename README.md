# Cadnano2 DNA Origami Design Software

## Overview
[Cadnano](http://cadnano.org/) is computer-aided design software for DNA origami nanostructures. The original citation is [here](https://academic.oup.com/nar/article/37/15/5001/2409858).

If you wish to use the newest version of Cadnano that supports Python scripting, see [cadnano2.5](https://github.com/cadnano/cadnano2.5/).

## Installation

**OS X**
* Install [homebrew](https://brew.sh/)
* Install python3: `brew install python3`
* Create and activate a virtual env: `python3 -m venv ~/virtualenvs/cn2 && source ~/virtualenvs/cn2/bin/activate`
* Install via pip: `pip3 install cadnano2`

**Windows**
* Download and install latest [python3](https://www.python.org/downloads/)
* `pip3 install cadnano2`

**Linux**
* Optional: Set up a [virtualenv](http://cadnano.readthedocs.io/en/master/virtualenv.html) (recommended)
* Clone git repo: `git clone https://github.com/douglaslab/cadnano2`

## Running
* Open the Terminal
* Activate virtual env: `source ~/virtualenvs/cn2/bin/activate`
* Run the app: `cadnano2`

## Environment vars

Some environment variables for debugging or customization:

* `CADNANO_DISCARD_UNSAVED`: Don't prompt the user to save unsaved changes; just exit.
* `CADNANO_DEFAULT_DOCUMENT` On creation of the default document, open the named file (put a path to the file in the value of the environment variable) instead of a blank document.
* `CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME`: Turn off other cadnano environment variables.

## Version notes

This version of Cadnano2 is being maintained by the [Douglas Lab](http://bionano.ucsf.edu/) to preserve the lattice-based design interface for research purposes. This is not a direct fork of [cadnano/cadnano2](https://github.com/cadnano/cadnano2) because that would result in a 200+ MB download when cloning. We have removed the [installer](https://github.com/cadnano/cadnano2/tree/master/installer) directory and git history, which makes this version less than 3 MB to download, or 11 MB uncompressed.

## License

This version of Cadnano2 is available under the MIT License.
GUI code that uses PyQt6 or PyQt3D is GPLv3 as [required](http://pyqt.sourceforge.net/Docs/PyQt6/introduction.html#license) by Riverbank Computing.
