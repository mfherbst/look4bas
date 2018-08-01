#!/usr/bin/env python3

import shutil
import re
from .elements import iupac_list

__strip_ANSI_escapes = re.compile(r"""
  \x1b     # literal ESC
  \[       # literal [
  [;\d]*   # zero or more digits or semicolons
  [A-Za-z] # a letter
  """, re.VERBOSE).sub


def printlen(s):
    """
    Return the printed length of a string
    """
    return len(__strip_ANSI_escapes("", s))


def crop_to_printlen(s, l):
    """Return only as many characters such that the printed length
    of them is less than or equal l"""
    if printlen(s) <= l:
        return s
    i = l
    while printlen(s[:i]) < l:
        i += 1
    return s[:i]


# Flags to influence the way basis sets are listed and how thay should be transformed
# to kwargs for colorise or print_basissets
__display_formats_base = {
    "elements": "show_elements",
    "colour": "use_colour",
    "crop": "crop_fields",
}


# Make sure that both positive and negative versions exist:
available_display_formats = [f for b in __display_formats_base for f in ("no-" + b, b)]


# Ansi colour escape sequences
colours_ANSI = {
    "yellow": '\033[93m',
    "white": '\033[0m',
    "green": '\033[92m',
    "red": '\033[91m',
    "cyan": '\033[96m',
}


def colorise(string, colour, **kwargs):
    """
    Use ANSI colour sequences to print a string in colour

    colour     Colour to use for printing
    kwargs         A list of keyword arguments, most importantly
                   if use_colour=False, than colourised printing is turned off.
    """
    if not kwargs.get("use_colour", True) or colour is None:
        return string
    else:
        return colours_ANSI[colour] + string + colours_ANSI["white"]


def parse_format_flags(format_flags):
    """Parse the format for the list_basissets function
    and return a dictionary key -> value from it"""
    ret = {}

    def negate_flag(flag):
        return flag[3:] if flag.find("no-") == 0 else "no-" + flag

    for flag in format_flags:
        if flag in __display_formats_base:
            kw = __display_formats_base[flag]
            ret[kw] = True
        elif negate_flag(flag) in __display_formats_base:
            kw = __display_formats_base[negate_flag(flag)]
            ret[kw] = False
        else:
            raise ValueError("Invalid format flag: {}".format(flag))
    return ret


def print_basissets(findings, highlight_atnums=[],
                    show_elements=False, use_colour=True, crop_fields=True,
                    source_to_colour=None):
    """
    Pretty print the basissets in the list
    highlight_atnums    Highlight these elements in the list
    show_elements       Print the list of elements
    use_colour          Use colour for printing
    crop_fields         Crop the output if it is too wide
    source_to_colour    Mapping from the source of the basis set
                        to an appropriate colour
    """
    # Get IUPAC element list
    elem_list = iupac_list()

    def format_element_list(basset):
        """
        Take a basis set dictionary and return a formatted string
        of the element list, taking the list of atnums to highlight into account.
        """
        atnum_symbols = [(e["atnum"], elem_list[e["atnum"]]["symbol"])
                         for e in basset["atoms"]]
        return ",".join(colorise(sym, "yellow", use_colour=use_colour)
                        if highlight_atnums and atnum in highlight_atnums
                        else sym for atnum, sym in atnum_symbols)

    # Determine maximal lengths of the strings we have:
    maxlen_name = max(1, max(len(bset["name"]) for bset in findings))
    maxlen_descr = max(1, max(len(bset["description"]) for bset in findings))

    # Ignore element string length if we don't care
    if show_elements:
        maxlen_elem = max(printlen(format_element_list(bset)) for bset in findings)
    else:
        maxlen_elem = 0

    # Adjust depending on width of terminal
    cols, _ = shutil.get_terminal_size(fallback=(120, 50))
    cols = max(120, cols)
    extra = 4  # What we need for column separators, ...

    if maxlen_name + maxlen_descr + maxlen_elem + extra > cols:
        # We don't crop the name ever, so compute the remainder:
        rem = cols - maxlen_name - extra

        if show_elements:
            # 2/3 for description, but only if its needed
            # and at least 1/3 for elements:
            maxlen_descr = min(maxlen_descr, max(50, 2 * rem // 3, rem - maxlen_elem - 1))
            maxlen_elem = max(50, rem - maxlen_descr)
        else:
            maxlen_descr = rem
            maxlen_elem = 0

    for bset in findings:
        # Maxlen values for this basis set
        # if colour is used, these values need to be altered
        # since ANSI colour escapes produce no "length" but count as a char
        maxlen = {"name": maxlen_name, "description": maxlen_descr,
                  "elements": maxlen_elem}

        fargs = {
            "description": bset["description"],
            "elements": format_element_list(bset),
            "name": bset["name"],
        }
        if source_to_colour:
            fargs["name"] = colorise(fargs["name"], source_to_colour.get(bset["source"]),
                                     use_colour=use_colour)

        if crop_fields:
            for key in fargs:
                if printlen(fargs[key]) > maxlen[key]:
                    fargs[key] = crop_to_printlen(fargs[key], maxlen[key] - 3)
                    if key in ["elements"]:
                        # Remove the half-printed element number after the last ","
                        icomma = fargs[key].rfind(",")
                        fargs[key] = fargs[key][:icomma] + "..."
                    else:
                        fargs[key] += "..."

        for key in fargs:
            maxlen[key] += len(fargs[key]) - printlen(fargs[key])

        # Build format string:
        fstr = "{name:" + str(maxlen["name"]) + "s}"
        fstr += "  {description:" + str(maxlen["description"]) + "s}"
        if show_elements:
            fstr += "  {elements:" + str(maxlen["elements"]) + "s}"

        print(fstr.format(**fargs))
