# look4bas
[![PyPI version](https://img.shields.io/pypi/v/look4bas.svg)](https://pypi.org/project/look4bas)

``look4bas`` is a Python script to search and obtain Gaussian basis sets.
Currently we use the data of the
[EMSL basis set exchange](https://bse.pnl.gov/bse/portal)
or the [ccrepo](http://grant-hill.group.shef.ac.uk/ccrepo/).

On the first invocation (and from there on in regular intervals) the script
consults both websites to download the current catalogue
of known basis sets.
Note, that the actual basis set data is not downloaded.
This is only done if the user uses the flag ``--download``, see below.

## Features
- Use **regular expressions** (``grep``) for basis set names and descriptions:
  ```bash
  look4bas  "double zeta"
  ```
- **Ignore case** when searching for patterns:
  ```bash
  look4bas "cc-pv.z" -i
  ```
- Limit to basis sets which **contain** basis definitions for specific **elements**
  (e.g. helium, neon and argon):
  ```bash
  look4bas --elements He Ne Ar
  ```
- Combine various filters:
  ```bash
  look4bas --elements H --regex "cc-pv.z" -i "zeta"
  ```
- Not only list the matching basis sets by name and give a short description
  for them, but also **list the elements** for which this basis set defines
  basis functions:
  ```bash
  look4bas "double zeta" --format elements
  ```
  The same thing can be achieved by using the pre-defined ``--extra`` output
  format style, i.e
  ```bash
  look4bas --extra "double zeta"
  ```
- **Download** the findings in Gaussian94 basis format to the current working directory:
  ```bash
  look4bas --elements H --regex "cc-pv.z" -i "zeta" --download
  ```
- For more info about the commandline flags ``look4bas`` understands,
  see the output of ``look4bas -h``

## Installation
Either you clone the repo and make sure you have the appropriate dependencies
installed (see next section), or you just use `pip`:
```
pip install look4bas
```

## Requirements and Python dependencies
- Python >= 3.4
- argparse
- [Beautiful Soup](https://pypi.python.org/pypi/beautifulsoup4) >= 4.2
- [requests](https://pypi.python.org/pypi/requests) >= 2.2
- shutil

## Citing
If you use the script and find it useful, please cite this software:
[![DOI](https://zenodo.org/badge/89177225.svg)](https://zenodo.org/badge/latestdoi/89177225)
