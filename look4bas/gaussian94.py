#!/usr/bin/env python3
from . import elements


NUMBER_TO_AM = ["S", "P", "D", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]


def __float_fortran(string):
    return float(string.replace("d", "e").replace("D", "E"))


def __strip_comments(string):
    """
    Strip all comments from the string
    """
    return "\n".join(e.strip() for e in string.split("\n") if e and e[0] != '!')


def __parse_contractions(lines, *outputs):
    for line in lines:
        exp_coeffs = line.split()
        if len(exp_coeffs) != len(outputs):
            raise ValueError("Not enough columns found. Expected {} columns, "
                             "but found only {}. Culprit line is "
                             "'{}'".format(len(outputs), len(exp_coeffs), line))
        try:
            for i in range(len(outputs)):
                outputs[i].append(__float_fortran(exp_coeffs[i]))
        except ValueError:
            raise ValueError("Could not convert columns to float. "
                             "Culprit line is '{}'".format(line))


def __parse_element_block(block, elem_symbols_lower):
    ret = {"functions": []}
    lines = [__strip_comments(l) for l in block.split("\n")]
    lines = [l for l in lines if len(l) > 0]

    symbol, _ = lines[0].split(maxsplit=1)
    try:
        ret["atnum"] = elem_symbols_lower.index(symbol.lower())
    except KeyError:
        raise ValueError("Element block starting with invalid element symbol "
                         "{}".format(symbol))

    idx = 1
    while idx < len(lines):
        # New function definition starts with angular momentum
        # and the number of contractions
        amstr, n_contr, _ = lines[idx].split(maxsplit=2)
        amstr = amstr.upper()

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
            __parse_contractions(lines[idx + 1:idx + n_contr + 1],
                                 exponents, s_coefficients, p_coefficients)

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
        else:
            # Standard cases:
            try:
                am = NUMBER_TO_AM.index(amstr)
            except ValueError:
                raise ValueError("Invalid angular momentum string {}".format(amstr))

            coefficients = []
            exponents = []
            __parse_contractions(lines[idx + 1:idx + n_contr + 1], exponents,
                                 coefficients)

            ret["functions"].append({
                "angular_momentum": am,
                "coefficients": coefficients,
                "exponents": exponents,
            })
            idx += n_contr + 1
    return ret


def loads(string, elem_list=elements.iupac_list()):
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
    blocks = [b.strip() for b in string.split("****")]

    if len(blocks) < 2:
        raise ValueError("At least one '****' sequence in the input string is expected")
    if len(__strip_comments(blocks[0])) > 0:
        raise ValueError("Found valid content before initial '****' sequence")
    if len(__strip_comments(blocks[-1])) > 0:
        raise ValueError("Found valid content after final '****' sequence")

    # Convert the elem_list to all-lower-case
    elem_symbols_lower = [e["symbol"].lower() for e in elem_list]

    # The first and last block are just comments or trailing newlines and can
    # be ignored
    return [__parse_element_block(block, elem_symbols_lower) for block in blocks[1:-1]]


def dumps(data, elem_list=elements.iupac_list()):
    """
    Take a list of dicts containing the entries
        atnum:     atomic number
        functions: list of dict with the keys:
            angular_momentum  Angular momentum of the function
            coefficients      List of contraction coefficients
            exponents         List of contraction exponents
    and dump a string representing this basis set definition
    in Gaussian94 format.
    """
    lines = []
    for atom in data:
        lines.append("****")
        lines.append(elem_list[atom["atnum"]]["symbol"] + "     0")
        for fun in atom["functions"]:
            lfun = len(fun["coefficients"])
            if lfun != len(fun["exponents"]):
                raise ValueError("Length of coefficients and length of exponents "
                                 "in contraction specification need to agree")

            am = NUMBER_TO_AM[fun["angular_momentum"]]
            lines.append(am + "   " + str(lfun) + "   1.00")

            for i, coeff in enumerate(fun["coefficients"]):
                exp = fun["exponents"][i]
                fmt = "{0:15.7f}             {1: #11.8G}"
                lines.append(fmt.format(exp, coeff))
    lines.append("****\n")
    return "\n".join(lines)
