from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='cadnano2',
    version='2.4.11',
    description='Cadnano2 for PyQt6',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/douglaslab/cadnano2',
    author='Shawn Douglas',
    author_email='shawn.douglas@ucsf.edu',
    license='MIT',
    packages=find_packages(),
    package_data={'cadnano2': ['ui/mainwindow/images/*.svg', 'ui/mainwindow/images/*.png']},
    install_requires=['PyQt6'],
    entry_points = {'console_scripts': ['cadnano2 = cadnano2.main:main']},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)

