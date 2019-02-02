#!/usr/bin/env python3
from .. import elements
from warnings import warn
import look4bas


def dumps(data, elem_list=elements.IUPAC_LIST, **kwargs):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in CFOUR format.

    Note, that as of now potential ECP data present in the basis
    is ignored.
    """
    warn("Dumping basis sets in CFOUR format is experimental.")
    name = kwargs.get("name", "look4bas")
    description = kwargs.get("description",
                             "Created by look4bas version "
                             "{}".format(look4bas.__version__))

    lines = []
    for atom in data:
        elem = elem_list[atom["atnum"]]["symbol"]
        functions = atom["functions"]

        # Construct the list of angular momenta present
        ams = sorted(set(fun["angular_momentum"] for fun in functions))

        # Number of contractions per am
        map_ncontr = {
            am: len([fun for fun in functions
                     if fun["angular_momentum"] == am])
            for am in ams
        }

        # Extract the list of (unique) exponents for each angular momentum
        map_exps = {
            am: sorted(set(exp for fun in functions
                           for exp in fun["exponents"]
                           if fun["angular_momentum"] == am),
                       reverse=True)
            for am in ams
        }

        # Output element, name and description
        lines.append("{}:{}".format(elem.upper(), name.upper()))
        lines.append(description)
        lines.append("")  # Empty line

        # Number of AMs, contractions and exponents
        lines.append("{:3d}".format(len(ams)))
        lines.append("".join("{:5d}".format(am) for am in ams))
        lines.append("".join("{:5d}".format(map_ncontr[am]) for am in ams))
        lines.append("".join("{:5d}".format(len(map_exps[am])) for am in ams))

        for am in ams:
            # Print exponents
            str_exp = ["{:14.7f}".format(exp) for exp in map_exps[am]]
            line_buffer = ""
            for i, exp in enumerate(str_exp):
                if i % 5 == 0:
                    lines.append(line_buffer)
                    line_buffer = ""
                line_buffer += exp
            if line_buffer:
                lines.append(line_buffer)

            # Print contractions as a matrix
            for exp in map_exps[am]:   # row
                line_buffer = ""
                for fun in functions:  # column
                    if fun["angular_momentum"] != am:
                        continue

                    # Find appropriate coefficient (or zero)
                    if exp in fun["exponents"]:
                        coeff = fun["coefficients"][fun["exponents"].index(exp)]
                    else:
                        coeff = 0.0
                    line_buffer += "{:10.7f} ".format(coeff)

                lines.append(line_buffer)

        # Finish atom with empty line
        lines.append("")

    # Finish basis sets with empty line
    lines.append("")
    return "\n".join(lines)
