#coding: utf-8
import os
from setuptools import setup, find_packages


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="fabric-coat",
    version="0.4.25",
    author="Rasmus Schlünsen, Mads Sülau Jørgensen, Martin Kjellberg",
    author_email="rs@konstellation.dk, msj@konstellation.dk, martin@martinkjellberg.com",
    description=("Deployment helpers for fabric3, forked from https://bitbucket.org/madssj/fabric-coat"),
    license="BSD",
    keywords="fabric coat deployment rsync helper",
    url="https://github.com/mistalaba/fabric-coat",
    packages=find_packages('src'),
    long_description=read('README'),
    package_dir={'': 'src'},
    install_requires=['fabric3 @ git+https://github.com/MUST-Digital/fabric.git', 'pydispatcher'],
)
