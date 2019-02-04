#!/usr/bin/env python3
from .. import elements
from .constants import NUMBER_TO_AM
from warnings import warn


def dumps(data, elem_list=elements.IUPAC_LIST, **kwargs):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in Turbomole format.

    Note, that as of now potential ECP data present in the basis
    is ignored.
    """
    warn("Dumping basis sets in Turbomole format is experimental.")
    name = kwargs.get("name", "look4bas")

    lines = []
    lines.append("$basis")
    for atom in data:
        lines.append("*")
        symbol = elem_list[atom["atnum"]]["symbol"].lower()
        lines.append("{} {}".format(symbol, name))
        lines.append("*")
        for fun in atom["functions"]:
            lfun = len(fun["coefficients"])
            if lfun != len(fun["exponents"]):
                raise ValueError("Length of coefficients and length of exponents "
                                 "in contraction specification need to agree.")

            am = NUMBER_TO_AM[fun["angular_momentum"]].lower()
            lines.append("  {:3d}  {}".format(lfun, am))

            for i, coeff in enumerate(fun["coefficients"]):
                exp = fun["exponents"][i]
                lines.append("     {0:15.7f}    {1: #11.8G}".format(exp, coeff))
    lines.append("*")

    for atom in data:
        if "ecp" in atom:
            warn(dumps.__name__ + " currently ignores any ECP "
                 "definitions parsed.")
            break

    lines.append("$end")
    return "\n".join(lines)
