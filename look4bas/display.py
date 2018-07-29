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


# Flags to influence the way basis sets are listed
__display_formats_base = ["elements", "colour", "crop"]


# Make sure that both positive and negative versions exist:
available_display_formats = [f for b in __display_formats_base for f in ("no-" + b, b)]


# Ansi colour escape sequences
colours_ANSI = {
    "yellow": '\033[93m',
    "white": '\033[0m',
}


def parse_list_format(format_list):
    """Parse the format for the list_basissets function
    and return a dictionary key -> value from it"""
    ret = {}

    def negate_flag(flag):
        return flag[3:] if flag.find("no-") == 0 else "no-" + flag

    for flag in format_list:
        if flag in __display_formats_base:
            ret[flag] = True
        elif negate_flag(flag) in __display_formats_base:
            ret[negate_flag(flag)] = False
    return ret


def print_basissets(findings, highlight_atnums=[],
                    elements=False, colour=True, crop=True,
                    source_to_colour=None):
    """
    Pretty print the basissets in the list
    highlight_atnums     Highlight these elements in the list
    elements        Print the list of elements
    colour          Use colour for printing
    crop            Crop the output if it is too wide
    source_to_colour    Mapping from the source of the basis set
                        to an appropriate colour
    """
    # Colours used for display
    creset = celem = cbas = ""
    if colour:
        creset = colours_ANSI["white"]
        celem = colours_ANSI["yellow"]
        cbas = colours_ANSI["yellow"]

    # Get IUPAC element list
    elem_list = iupac_list()

    def format_element_list(basset):
        """
        Take a basis set dictionary and return a formatted string
        of the element list, taking the list of atnums to highlight into account.
        """
        atnum_symbols = [(e["atnum"], elem_list[e["atnum"]]["symbol"])
                         for e in basset["atoms"]]
        return ",".join(celem + sym + creset if atnum in highlight_atnums
                        else sym for atnum, sym in atnum_symbols)

    # Determine maximal lengths of the strings we have:
    maxlen_name = max(1, max(len(bset["name"]) for bset in findings))
    maxlen_descr = max(1, max(len(bset["description"]) for bset in findings))

    # Ignore element string length if we don't care
    if elements:
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

        if elements:
            # 2/3 for description, but only if its needed
            # and at least 1/3 for elements:
            maxlen_descr = min(maxlen_descr, max(50, 2 * rem // 3, rem - maxlen_elem - 1))
            maxlen_elem = max(50, rem - maxlen_descr)
        else:
            maxlen_descr = rem
            maxlen_elem = 0

    # Build format string:
    fstr = cbas + "{name:" + str(maxlen_name) + "s}" + creset
    fstr += "  {description:" + str(maxlen_descr) + "s}"
    if elements:
        fstr += "  {elements:" + str(maxlen_elem) + "s}"

    for bset in findings:
        descr = bset["description"]
        elems = format_element_list(bset)
        if crop:
            if printlen(descr) > maxlen_descr:
                descr = crop_to_printlen(descr, maxlen_descr - 3)
                descr += "..."
            if printlen(elems) > maxlen_elem:
                elems = crop_to_printlen(elems, maxlen_elem - 3 + 1)
                # Remove the half-printed element number after the last ","
                elems = elems[:elems.rfind(",")]
                elems += "..."

        print(fstr.format(name=bset["name"], description=descr, elements=elems))
