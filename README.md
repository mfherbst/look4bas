# look4bas

``look4bas`` is a Python script to search and obtain Gaussian basis sets.
Currently we only use the data of the
[EMSL basis set exchange](https://bse.pnl.gov/bse/portal).

On the first invocation (and from there on in regular intervals) the script
consults the EMSL BSE website to download the current catalogue
of known basis sets.
Note, that the actual basis set data is not downloaded.
This is only done if the user uses the flag ``--download``, see below.

## Features
- Use regular expressions (``grep``) for basis set names and descriptions
  ```bash
  look4bas  "double zeta"
  ```
- Ignore case when searching for patterns:
  ```bash
  look4bas "cc-pv.z" -i
  ```
- Limit to basis sets containing certain elements
  ```bash
  look4bas --elements He Ne Ar
  ```
- Combine various filters:
  ```bash
  look4bas --elements H --regex "cc-pv.z" -i "zeta"
  ```
- Download the findings in Gaussian94 format to the current working directory
  ```bash
  look4bas --elements H --regex "cc-pv.z" -i "zeta" --download
  ```
- Print not only the list of basis sets and descriptions, but also the
  elements which are present in the basis sets
  ```bash
  look4bas --print-elements  "double zeta"
  ```
- For more info about the commandline flags ``look4bas`` understands,
  see the output of ``look4bas -h``
