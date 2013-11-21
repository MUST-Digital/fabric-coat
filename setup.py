#coding: utf-8
import os
from setuptools import setup, find_packages


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name="fabric-coat",
    version="0.4.10",
    author="Rasmus Schlünsen, Mads Sülau Jørgensen",
    author_email="rs@konstellation.dk, msj@konstellation.dk",
    description=("Deployment helpers for fabric"),
    license="BSD",
    keywords="fabric coat deployment rsync helper",
    url="https://bitbucket.org/madssj/fabric-coat",
    packages=find_packages('src'),
    long_description=read('README'),
    package_dir={'': 'src'},
    install_requires=['fabric >= 1.3', 'pydispatcher'],
)
