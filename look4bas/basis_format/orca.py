#!/usr/bin/env python3
from .constants import NUMBER_TO_AM
from warnings import warn


def dumps(data, **kwargs):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in the format expected by the Orca quantum chemistry program.

    Note, that as of now potential ECP data present in the basis
    is ignored.
    """
    lines = []
    lines.append("%basis")
    for atom in data:
        lines.append("NewGTO {}".format(atom["atnum"]))
        for fun in atom["functions"]:
            lfun = len(fun["coefficients"])
            if lfun != len(fun["exponents"]):
                raise ValueError("Length of coefficients and length of exponents "
                                 "in contraction specification need to agree")

            am = NUMBER_TO_AM[fun["angular_momentum"]]
            lines.append(" {}    {}".format(am, lfun))

            for i, coeff in enumerate(fun["coefficients"]):
                exp = fun["exponents"][i]
                fmt = " {0:2d} {1:15.7f}    {2: #11.9G}"
                lines.append(fmt.format(i + 1, exp, coeff))
        lines.append("end")
        if "ecp" in atom:
            warn(dumps.__name__ + " currently ignores any ECP "
                 "definitions.")
    lines.append("end")

    return "\n".join(lines)
