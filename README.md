# look4bas
[![PyPI version](https://img.shields.io/pypi/v/look4bas.svg)](https://pypi.org/project/look4bas)

``look4bas`` is a Python script to search and obtain Gaussian basis sets.
Currently we use the data of the
[EMSL basis set exchange](https://bse.pnl.gov/bse/portal)
or the [ccrepo](http://grant-hill.group.shef.ac.uk/ccrepo/).
An API to interact with the script directly from a `python` script
on a high level is provided as well, see below.

On the first invocation (and from there on in regular intervals) the script
downloads an archived catalogue of known basis sets to enable to search for
them locally and on the commandline.
Note, that the actual basis set data is not downloaded.
This is only done if the user uses the flag ``--download``, see below.

## Commandline features
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
  Notice, that this will download the basis set definitions for all elements,
  for which this basis set is known at the corresponding source,
  even if once uses ``--elements`` to filter for particular elements.

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

## Python API
Searching for basis sets can be accomplished directly via a `python` API as well,
which will return the search results in dictionaries.
An example can be found below, which is also available in the example file
[`examples/python_api_example.py`](examples/python_api_example.py).
```python
import look4bas

# Search for a basis set which has helium and beryllium
# and which matches the regular expression '^cc-pv.z'
# ignoring case.
db = look4bas.Database()
findings = db.search_basisset(pattern="^cc-pv.z", ignore_case=True,
                              regex=True, has_atnums=[2, 4])

if not findings:
    print("Found nothing")

# Pick the first finding
bset = findings[0]

# Print metadata
print("Basis set name:         ", bset["name"])
print("Basis set description:  ", bset["description"])

# Retrieve full basis set information online
bset = db.lookup_basisset_full(bset)

# Build a mapping from the atom number to the list
# of contracted basis functions
num_map = {at["atnum"]: at["functions"] for at in bset["atoms"]}

# Build mapping from the atom symbol to the list
# of contracted basis functions
element_list = look4bas.elements.iupac_list()
symbol_map = {element_list[atnum]["symbol"]: functions
              for atnum, functions in num_map.items()}

# Print basis set for the helium atom
print("Basis definition for helium:")
print(symbol_map["He"])
```

## Citing
If you use the script and find it useful, please cite this software:
[![DOI](https://zenodo.org/badge/89177225.svg)](https://zenodo.org/badge/latestdoi/89177225)
