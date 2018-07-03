"""Setup for look4bas"""

# Use setuptools for these commands (they don't work well or at all
# with distutils).  For normal builds use distutils.
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='look4bas',
      packages=['look4bas'],
      version='0.0.0',
      description='Command line tool to search for contracted Gaussian-type basis sets '
      'in electronic structure theory',
      url='https://github.com/mfherbst/look4bas',
      install_requires=['PyYAML (>=3.10)', 'requests (>=2.2)', 'beautifulsoup4 (>= 4.2)'],
      python_requires='>=3',
      classifiers=[],
      )
