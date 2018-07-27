#!/usr/bin/env python3
from . import element


def __float_fortran(string):
    return float(string.replace("d", "e").replace("D", "E"))


def __strip_comments(string):
    """
    Strip all comments from the string
    """
    return "\n".join(e.strip() for e in string.split("\n") if e and e[0] != '!')


def __parse_element_block(block):
    ret = {"functions": []}
    lines = [__strip_comments(l) for l in block.split("\n")]
    lines = [l for l in lines if len(l) > 0]

    symbol, _ = lines[0].split(maxsplit=1)
    try:
        ret["atnum"] = element.by_symbol(symbol).atom_number
    except KeyError:
        raise ValueError("Element block starting with invalid element symbol "
                         "{}".format(symbol))

    number_to_am = ["s", "p", "d", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o"]
    idx = 1
    while idx < len(lines):
        # New function definition starts with angular momentum
        # and the number of contractions
        amstr, n_contr, _ = lines[idx].split(maxsplit=2)
        amstr = amstr.lower()

        try:
            n_contr = int(n_contr)
        except ValueError:
            raise ValueError("Expect number of contracted function (following AM letter) "
                             "to be an integer, not {}".format(n_contr))

        if amstr == "sp":
            # This is a special case, where an s and p shell are defined
            # at the same time.

            s_coefficients = []
            p_coefficients = []
            exponents = []
            for i in range(n_contr):
                line = lines[idx + i + 1]
                exp_coeffs = line.split()

                if len(exp_coeffs) != 3:
                    raise ValueError("Expect exactly three columns in sp "
                                     "contraction block. "
                                     "Culprit line is '{}'".format(line))

                try:
                    exponents.append(__float_fortran(exp_coeffs[0]))
                    s_coefficients.append(__float_fortran(exp_coeffs[1]))
                    p_coefficients.append(__float_fortran(exp_coeffs[2]))
                except ValueError:
                    raise ValueError("Could not convert to float: {}. "
                                     "Culprit line is '{}'".format(exp_coeffs, line))

            ret["functions"].append({
                "angular_momentum": 0,
                "coefficients": s_coefficients,
                "exponents": exponents,
            })
            ret["functions"].append({
                "angular_momentum": 1,
                "coefficients": p_coefficients,
                "exponents": exponents,
            })
            idx += n_contr + 1
            continue

        # Standard cases:
        try:
            am = number_to_am.index(amstr)
        except ValueError:
            raise ValueError("Invalid angular momentum string {}".format(amstr))

        coefficients = []
        exponents = []
        for i in range(n_contr):
            line = lines[idx + i + 1]
            exp_coeff = line.split()

            if len(exp_coeff) != 2:
                raise ValueError("Expect exactly two columns in contraction block. "
                                 "Culprit line is '{}'".format(line))

            try:
                exponents.append(__float_fortran(exp_coeff[0]))
                coefficients.append(__float_fortran(exp_coeff[1]))
            except ValueError:
                raise ValueError("Could not convert to float: {}. "
                                 "Culprit line is '{}'".format(exp_coeff, line))

        ret["functions"].append({
            "angular_momentum": am,
            "coefficients": coefficients,
            "exponents": exponents,
        })
        idx += n_contr + 1
    return ret


def parse_g94(string):
    """
    Parse a string, which represents a basis set file in g94
    format and return the defined basis functions
    as a a list of dicts containing the following entries:
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents

    The format is roughly speaking:
      ****
      Element_symbol
      AM   n_contr
         exp1     coeff1
         exp2     coeff2
      AM2  n_contr
         exp1     coeff1
         exp2     coeff2
      ****
      Element_symbol
      ...

    where
       Element_symbol    a well-known element symbol
       AM                azimuthal quantum number as a symbol for angular momentum
       n_contr           number of contracted primitives
       exp1              exponents
       coeff1            corresponding contraction coefficients.

    All element blocks are separated by '****'. The numbers for exp and coeff
    may be given in the Fortran float convention (using 'D's instead of 'E's).
    """

    # First split into blocks at the separating "****)
    blocks = string.split("****\n")

    if len(blocks) < 2:
        raise ValueError("At least one '****' sequence in the input string is expected")
    if len(__strip_comments(blocks[0])) > 0:
        raise ValueError("Found valid content before initial '****' sequence")
    if len(__strip_comments(blocks[-1])) > 0:
        raise ValueError("Found valid content after final '****' sequence")

    # The first and last block are just comments or trailing newlines and can
    # be ignored
    return [__parse_element_block(block) for block in blocks[1:-1]]
