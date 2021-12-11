from setuptools import setup, find_packages

setup(
    name='cadnano2',
    version='2.1',    
    description='Cadnano2 for PyQt6',
    url='https://github.com/douglaslab/cadnano2',
    author='Shawn Douglas, Nick Conway',
    author_email='shawn.douglas@ucsf.edu',
    license='MIT',
    packages=find_packages(),
    install_requires=['PyQt6'],
    entry_points = {'console_scripts': ['cadnano2 = cadnano2.main:main']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.9',
    ],
)

