# Cadnano2 DNA Origami Software (PyQt5 port)

## Overview
[Cadnano](http://cadnano.org/) is computer-aided design software for DNA origami nanostructures. The original citation is [here](https://academic.oup.com/nar/article/37/15/5001/2409858).

This version of Cadnano2 is being maintained by the [Douglas Lab](http://bionano.ucsf.edu/) to preserve the lattice-based design interface for research purposes. This is not a direct fork of [cadnano/cadnano2](https://github.com/cadnano/cadnano2) because that would result in a 200+ MB download when cloning. We have removed the [installer](https://github.com/cadnano/cadnano2/tree/master/installer) directory and git history, which makes this version less than 3 MB to download, or 11 MB uncompressed.

If you wish to use the newest version of Cadnano that supports Python scripting and non-lattice designs, see [cadnano2.5](https://github.com/cadnano/cadnano2.5/).

## Installation

**OS X**
* Install [homebrew](https://brew.sh/)
* Install python3: `brew install python3`
* Optional: Set up a [virtualenv](http://cadnano.readthedocs.io/en/master/virtualenv.html) (recommended)
* Install dependencies: `pip3 install PyQt5 networkx`
* Clone git repo: `git clone https://github.com/douglaslab/cadnano2`

**Windows**
* Download and install latest [python3](https://www.python.org/downloads/)
* Optional: Set up a [virtualenv](http://cadnano.readthedocs.io/en/master/virtualenv.html) (recommended)
* `pip3 install PyQt5 networkx`

**Linux**
* Optional: Set up a [virtualenv](http://cadnano.readthedocs.io/en/master/virtualenv.html) (recommended)
* Install dependencies: `pip3 install PyQt5 networkx`
* Clone git repo: `git clone https://github.com/douglaslab/cadnano2`

## Running
* Open the terminal and navigate to the path of the cadnano2 git repo.
* `python3 main.py`

## Environment vars

Some environment variables for debugging or customization:

* `CADNANO_DISCARD_UNSAVED`: Don't prompt the user to save unsaved changes; just exit.
* `CADNANO_DEFAULT_DOCUMENT` On creation of the default document, open the named file (put a path to the file in the value of the environment variable) instead of a blank document.
* `CADNANO_IGNORE_ENV_VARS_EXCEPT_FOR_ME`: Turn off other cadnano environment variables.

## License

This version of Cadnano2 is available under the MIT License.
GUI code that uses PyQt5 or PyQt3D is GPLv3 as [required](http://pyqt.sourceforge.net/Docs/PyQt5/introduction.html#license) by Riverbank Computing.
