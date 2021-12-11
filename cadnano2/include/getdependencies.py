#!/usr/bin/env python
# encoding: utf-8

from .fetchfile import fetchFile
import shutil
from os.path import basename, dirname, splitext, exists, split, abspath
import os

# list of tuples of the url and the subdirectory to copy to the include directory
urls = [('http://pypi.python.org/packages/source/n/networkx/networkx-1.6.tar.gz', 'networkx')
        ]

# this is intended to be run in the include folder of cadnano2
if __name__ == '__main__':
    for urlBlock in urls:
        url, subfolder_name = urlBlock
        filename = basename(url)
        base_url = dirname(url)
        folder = fetchFile(filename, base_url)
        this_dirname, this_filename = split(abspath(__file__))
        os.chdir(this_dirname)
        if subfolder_name:
            subfolder_path = folder + '/' + subfolder_name
            # remove existing folder
            if os.path.exists(subfolder_name):
                print("file exists")
                shutil.rmtree(subfolder_name)
            else:
                print("file does not exist", subfolder_name)
            shutil.move(subfolder_path, subfolder_name)
            shutil.rmtree(folder)
    # end for
