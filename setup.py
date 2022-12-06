#!/usr/bin/env python3

import os
import sys

if len(sys.argv) == 1:
    os.system('%s sdist' % sys.argv[0])
    os.system('twine upload dist/*')
    os.system('rm -rf dist *.egg-info')
    exit(0)


from pathlib import Path
from setuptools import setup

from teslapi import TESLAPI_VERSION

setup(
    name='teslapi',
    description='Tesla API Service',
    version=TESLAPI_VERSION,
    license='MIT',
    author='Yonsm',
    author_email='Yonsm@qq.com',
    url='https://github.com/Yonsm/TeslaPi',
    long_description=Path('README.md').read_text(),
    long_description_content_type='text/markdown',
    packages=['teslapi'],
    scripts=['tecli.py'],
    python_requires='>=3.7',
    install_requires=['httpx'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
