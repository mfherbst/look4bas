""" Dictionary of the basis set formats supported by this script,
    mapped to the default file extension used.
"""
extension = {
    "cfour": "cfour",
    "gaussian94": "g94",
    "nwchem": "nwchem",
    "orca": "orca",
    "qchem": "qchem",
    "turbomole": "turbomole",
}


def dumps(format, data):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in the specified format.
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
    return dumps[format](data)
