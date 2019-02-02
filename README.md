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
- Python >= 3.5 (Note: python 3.4. could work as well)
- [Beautiful Soup](https://pypi.org/project/beautifulsoup4) >= 4.2
- [lxml](https://pypi.org/project/lxml) (>= 4.2)
- [requests](https://pypi.org/project/requests) >= 2.2


## Python API
Searching for basis sets can be accomplished directly via a `python` API,
which will return the search results in plain `python` dictionaries and lists.
An example for such use can be found in
[`examples/python_api.py`](examples/python_api.py).


## Using look4bas with ...
This section contains some hints how to use `look4bas` specifically
in combination with a few quantum-chemistry programs. If you use it
with other codes or feel some explanation is missing,
feel free to extend it here with a PR.

### CFOUR
The CFOUR format is implemented, but not properly tested
so far. Feel free to use it and please get in touch if you encounter
problems.

### Gaussian
```
TODO
```


### NWChem
```
TODO
```

### ORCA
Here `look4bas` downloads the basis set in the format expected
for a `%basis` block. By concatenation with a skeleton
input file, which defines the rest of the calculation parameters,
one can therefore quickly prepare an input file for
[Orca](https://orcaforum.kofo.mpg.de/).

For example, consider a water geometry optimisation using `pc-2`.

1. Define a skeleton ORCA input file `water_skel.in`
```
! hf opt
* xyz 0 1
  H 1 0 0
  H 0 1 0
  O 0 0 0
*
```

2. Download the pc-2 basis with `look4bas`
```
look4bas "^pc-2$" --elem H O Fe --down orca
```

3. Create the actual input file
```
cat water_skel.in pc-2.orca water.in
```

4. Run ORCA
```
orca water.in | tee water.out
```


### pyscf
```
TODO
```

### Q-Chem
`look4bas` directly downloads a basis set in the format expected
in a `$basis` section of a [Q-Chem](https://q-chem.com) input file.
Therefore one may simply concatenate a
basis set definition downloaded with `look4bas`
with a skeleton input file, which configures the rest of the
calculation.

For example, we consider again a simple water geometry optimisation.

1. We define a skeleton Q-Chem input file `water_skel.qcin`:
```
$molecule
0 1
  H 1 0 0
  H 0 1 0
  O 0 0 0
$end

$rem
    exchange  hf
    basis     gen
    jobtype   opt
$end
```
2. We download, for example, the pc-2 basis with `look4bas`
```bash
look4bas "^pc-2$" --elem H O Fe --down qchem
```
3. Finally the actual Q-Chem input file `water.qcin` of such a
job, using exactly the downloaded basis, can be created
just by:
```
cat water_skel.qcin pc-2.bas > water.qcin
```

### Turbomole
The Turbomole format is implemented, but not properly tested
so far. Feel free to use it and please get in touch if you encounter
problems.


## Citing
If you use the script for your research, please cite this software:
[![DOI](https://zenodo.org/badge/89177225.svg)](https://zenodo.org/badge/latestdoi/89177225)
