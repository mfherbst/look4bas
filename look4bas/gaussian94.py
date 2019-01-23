#!/usr/bin/env python3
from . import elements
from warnings import warn


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
            raise ValueError("Expect number of contracted function"
                             " (following AM letter) "
                             "to be an integer, not {}".format(n_contr))

        if amstr == "SP":
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


def __is_ecp_section(final_block, cgtos, elem_symbols_lower):
    # final_block is an ECP section, if the 0th line
    # marks an element, which already exists in the cgtos array.
    # Furthermore the 1th and 4th line should have exactly
    # 3 fields

    lines = final_block.split("\n")
    if len(lines) < 5:
        return False  # Not enough lines

    line0 = lines[0].split()  # Element 0
    line1 = lines[1].split()  # Name L Nelec
    line4 = lines[4].split()  # power exponent coefficient
    if len(line0) != 2 or len(line1) != 3 or len(line4) != 3:
        return False

    element = line0[0].strip().lower()
    try:
        atnum = elem_symbols_lower.index(element.lower())
    except KeyError:  # Not a valid element symbol
        return False
    return atnum in cgtos  # Atnum should have appeared already


def __parse_ecp_section(ecp_block, elem_symbols_lower):
    lines = ecp_block.split("\n")

    # Loop to parse one record at a time
    ret = []
    i = 0
    while i < len(lines):
        error = "Error in ECP block number " + str(len(ret) + 1) + \
                ", starting with '" + lines[i] + "'"

        record = {}
        ecp = record["ecp"] = {}

        if i + 1 >= len(lines):
            raise ValueError(error + ": Block terminated prematurely by EOF")

        # Line 0: Contains atom symbol and a "0"
        line0 = lines[i + 0].split()
        if len(line0) != 2:
            raise ValueError(error + ": Expected 2 fields in first line, "
                             "not {}".format(len(line0)))
        if line0[1].strip() != "0":
            raise ValueError(error + ": Unexpected format in first line.")
        try:
            record["atnum"] = elem_symbols_lower.index(line0[0].lower())
        except KeyError:
            raise ValueError("Block starting with invalid element symbol "
                             "{}".format(line0[0]))

        # Line 1: Contains ECP name, maximal AM effected by ECP and
        #         number of electrons removed by ECP
        line1 = lines[i + 1].split()
        if len(line1) != 3:
            raise ValueError(error + ": Expected 3 fields in second line, "
                             "not {}".format(len(line1)))
        ecp["name"] = line1[0].strip()
        try:
            ecp["max_angular_momentum"] = int(line1[1].strip())
            ecp["n_electrons_removed"] = int(line1[2].strip())
        except ValueError:
            raise ValueError(error + ": Unexpected format of second line ' {}"
                             "'.".format(line1))

        i += 2  # First two lines have been dealt with

        # Parse ECP radial parts
        ecp["radial_parts"] = []
        for am in range(ecp["max_angular_momentum"] + 1):
            if i + 1 >= len(lines):
                raise ValueError(error + ": Block terminated prematurely "
                                 "while parsing ecp radial parts")

            title = lines[i]
            try:
                n_components = int(lines[i + 1])
            except ValueError:
                raise ValueError(error + ": Expect the number of components in "
                                 "an ECP function (value in the line following "
                                 "the title) to be an integer, not {}"
                                 "".format(n_components))

            i += 2  # Dealt with another two lines
            if i + n_components > len(lines):
                raise ValueError(error + ": Block terminated prematurely "
                                 "while parsing components of the {}th ECP "
                                 "radial part".format(am + 1))

            powers = []
            exponents = []
            coefficients = []
            for c in range(n_components):
                power_exponent_coeff = lines[i + c].split()
                if len(power_exponent_coeff) != 3:
                    raise ValueError(error + ": Did not find enough columns "
                                     "when parsing components of the {}th ECP "
                                     "function. Culprit line is '{}'"
                                     "".format(am + 1, lines[i + c]))
                try:
                    powers.append(int(power_exponent_coeff[0]))
                    exponents.append(__float_fortran(power_exponent_coeff[1]))
                    coefficients.append(__float_fortran(power_exponent_coeff[2]))
                except ValueError:
                    raise ValueError(error + ": Could not convert columns to "
                                     "int or float when parsing components of "
                                     "the {}th ECP function. "
                                     "Culprit line is '{}'"
                                     "".format(am + 1, lines[i + c]))

            i += n_components  # Advance lines

            ecp["radial_parts"].append({
                "polynomial_powers": powers,
                "gaussian_exponents": exponents,
                "coefficients": coefficients,
                "title": title,
            })
        ret.append(record)
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
        ecp:       Dict with the keys:
            max_angular_momentum    Maximal angular momentum altered by the ECP
            n_electrons_removed     Number of electrons removed by the ECP
            name                    Name of the ECP
            radial_parts            Radial parts of the ECP, list of dicts with
                coefficients           Coefficients of the radial fctn
                gaussian_exponents     Exponents of the Gaussian
                polynomial_powers      Powers of the radial factor r^l
                title                  Title of this term

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
    # Since ECPs are appended to the final "****", it could happen that there is
    # indeed valid content after the final "****"

    # Convert the elem_list to all-lower-case
    elem_symbols_lower = [e["symbol"].lower() for e in elem_list]

    # The first and last block are just comments or trailing newlines or
    # ECP definitions and can be ignored for getting the cgto information
    cgtos = {}
    for block in blocks[1:-1]:
        elem = __parse_element_block(block, elem_symbols_lower)
        cgtos[elem["atnum"]] = elem

    final_block = __strip_comments(blocks[-1])
    if len(final_block) == 0:
        ecps = {}
    elif __is_ecp_section(final_block, cgtos, elem_symbols_lower):
        ecps = __parse_ecp_section(final_block, elem_symbols_lower)
        ecps = {ecp["atnum"]: ecp for ecp in ecps}
    else:
        raise ValueError("Found content after final '****' sequence, "
                         "which does not appear to be an ECP definition")

    # Merge cgtos and ecps dictionaries
    ret = []
    for k in set(cgtos.keys()).union(set(ecps.keys())):
        item = cgtos.get(k, {})
        item.update(ecps.get(k, {}))
        ret.append(item)
    return ret


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

    Note, that as of now potential ECP data present in the basis
    is ignored.
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
        if "ecp" in atom:
            warn("look4bas.gaussian94.dumps currently ignores any ECP "
                 "definitions parsed.")
    lines.append("****\n")

    return "\n".join(lines)
