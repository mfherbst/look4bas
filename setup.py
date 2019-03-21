#!/usr/bin/env python3

"""Setup for look4bas"""
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


#
# Main setup code
#
long_description = """
Command line tool to search for contracted Gaussian-type basis
sets in electronic structure theory
""".strip()

setup(
    name='look4bas',
    description="Search for Gaussian basis sets",
    long_description=long_description,
    #
    url='https://github.com/mfherbst/look4bas',
    author='Michael F. Herbst',
    author_email="info@michael-herbst.com",
    license="GPL v3",
    #
    packages=find_packages(exclude=["*.test*", "test"]),
    scripts=["bin/look4bas"],
    version='0.3.1',
    #
    python_requires='>=3.5',
    install_requires=[
        'requests (>=2.2)',
        'beautifulsoup4 (>= 4.2)',
        'lxml (>= 4.2)'
    ],
    tests_require=["pytest"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Science/Research',
        "Topic :: Scientific/Engineering :: Chemistry",
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: Unix',
    ],
    #
    cmdclass={"pytest": PyTest},
)
