""" Dictionary of the basis set formats supported by this script,
    mapped to the default file extension used.
"""
extension = {
    "cfour": "GENBAS",
    "gaussian94": "g94",
    "nwchem": "nw",
    "orca": "orca",
    "qchem": "bas",
    "turbomole": "turbomole",
}


def dumps(format, data, name=None, description=None):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in the specified format.

    Optionally name and description of the basis set may be specified
    as well. Not all basis set formats use this information in the
    returned string, however.
    """
    from . import cfour, gaussian94, nwchem, orca, pyscf, qchem, turbomole

    dumps = {
        "cfour": cfour.dumps,
        "gaussian94": gaussian94.dumps,
        "nwchem": nwchem.dumps,
        "orca": orca.dumps,
        "qchem": qchem.dumps,
        "turbomole": turbomole.dumps,
        "pyscf": pyscf.dumps,
    }
    if format not in dumps:
        raise NotImplementedError("dumps for format {} is not implemented."
                                  "".format(format))
    return dumps[format](data, name=name, description=description)


def convert_to(package, data):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and convert them to the python datastructures used by a different
    program package.
    """
    from . import pyscf
    convert = {
        "pyscf": pyscf.convert_to,
    }
    if package not in convert:
        raise NotImplementedError("convert_to for package '{}' is not implemented."
                                  "".format(package))
    return convert[package](data)
