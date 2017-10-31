#!/usr/bin/env python3

# This script is an old relict from back in the days when look4bas
# was only a single script file. It should be split up sensibly.

import os
import re
import argparse
import shutil
from . import config, emsl, cache


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
__list_formats_base = ["elements", "colour", "crop"]


# Make sure that both positive and negative versions exist:
available_list_formats = [f for b in __list_formats_base for f in ("no-" + b, b)]


def parse_list_format(format_list):
    """Parse the format for the list_basissets function
    and return a dictionary key -> value from it"""
    ret = {flag: None for flag in __list_formats_base}

    def negate_flag(flag):
        return flag[3:] if flag.find("no-") == 0 else "no-" + flag

    for flag in format_list:
        if flag in __list_formats_base:
            ret[flag] = True
        elif negate_flag(flag) in __list_formats_base:
            ret[negate_flag(flag)] = False
    return ret


def list_basissets(l, highlight_elements=[], fmt=[]):
    """
    Pretty print the basissets in the list
    highlight_elements    Highlight these elements in the list
    fmt    The format to use for printing
    """
    # Parse the format flags:
    fmt_flags = parse_list_format(fmt)

    print(len(l), "basis sets matched your search:")

    # TODO improve this method ... it really is a compound of a hell lot of code

    # Colours:
    yellow = white = ""
    if fmt_flags["colour"]:
        yellow = '\033[93m'
        white = '\033[0m'

    # Determine maximal lengths of the strings we have:
    maxlen_name = 0
    maxlen_descr = 0
    maxlen_elem = 0
    for bset in l:
        maxlen_name = max(maxlen_name, len(bset["name"]))
        maxlen_descr = max(maxlen_descr, len(bset["description"]))
        maxlen_elem = max(maxlen_elem, len(",".join(bset["elements"])))

    # Ignore element string length if we don't care
    if not fmt_flags["elements"]:
        maxlen_elem = 0

    # Adjust depending on width of terminal
    cols, _ = shutil.get_terminal_size(fallback=(120, 50))
    cols = max(120, cols)
    extra = 4  # What we need for column separators, ...

    if maxlen_name + maxlen_descr + maxlen_elem + extra > cols:
        # We don't crop the name ever, so compute the remainder:
        rem = cols - maxlen_name - extra

        if fmt_flags["elements"]:
            # 2/3 for description, but only if its needed
            # and at least 1/3 for elements:
            maxlen_descr = min(maxlen_descr, max(50, 2 * rem // 3, rem - maxlen_elem - 1))
            maxlen_elem = max(50, rem - maxlen_descr)
        else:
            maxlen_descr = rem
            maxlen_elem = 0

    # Build format string:
    fstr = yellow + "{name:" + str(maxlen_name) + "s}" + white
    fstr += "  {description:" + str(maxlen_descr) + "s}"
    if fmt_flags["elements"]:
        fstr += "  {elements:" + str(maxlen_elem) + "s}"

    for bset in l:
        elems = ",".join([
            yellow + e + white if e in highlight_elements else e for e in bset["elements"]
        ])
        descr = bset["description"]

        if fmt_flags["crop"]:
            if printlen(descr) > maxlen_descr:
                descr = crop_to_printlen(descr, maxlen_descr - 3)
                descr += "..."
            if printlen(elems) > maxlen_elem:
                elems = crop_to_printlen(elems, maxlen_elem - 3 + 1)
                # Remove the half-printed element number after the last ","
                elems = elems[:elems.rfind(",")]
                elems += "..."

        print(fstr.format(name=bset["name"], description=descr, elements=elems))


def normalise_name(name):
    """Normalise a basis set name to yield a valid filename"""
    return "".join(["I" if c == "/" else c for c in name.lower()])


def download_basissets(l, fmt, destination="."):
    """Download all basis sets in the list using the supplied format
    (in optimally contracted form).
    """
    print("Downloading " + str(len(l)) + " basis sets in " + fmt + " format:")
    for b in l:
        path = destination + "/" + normalise_name(b["name"]) + "." + emsl.formats[fmt]

        if os.path.exists(path):
            print("   Warn: Skipping " + path + " since file already exists")
            continue

        print("   ", b["name"], " to ", path)
        data = emsl.download_basisset(b, fmt)
        open(path, "w").write(data)


def main():
    parser = argparse.ArgumentParser(
        description="Commandline tool to search and download Gaussian basis sets. "
        "The tool downloads (and caches) the list of basis sets from the emsl basis set "
        "exchange (https://bse.pnl.gov/bse/portal) for offline search and allows to "
        "easily download individual basis sets from it.",
    )

    parser.add_argument("--force-update", action="store_true",
                        help="Force the cached EMSL BSE database to be updated.")
    parser.add_argument("--destination", default=".", type=str, metavar="directory",
                        help="When downloading basis sets using --download store them in "
                        "this directory. (Default: '.', i.e. the current working "
                        "directory")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action='store_true', help="List the matching basis "
                      "sets (Default)")
    mode.add_argument("--download", nargs="*", metavar='format',
                      choices=emsl.formats.keys(),
                      help="Download the matching basis sets in the requested formats "
                      "(Default: " + " ".join(config.default_download_formats) + ") " +
                      "to the directory specified by --destination. ")

    #
    # Filter options
    #
    filters = parser.add_argument_group("Basisset filters")
    filters.add_argument("pattern", nargs='?', default=None, type=str,
                         help="A regular expression to match against the basis set name "
                         "*or* the description. So if either description or basis set "
                         "name matches this, the basis set is considered a match.")
    filters.add_argument("--elements", metavar="element", nargs='+',
                         help="List of elements the basis set should contain. "
                         "Implies '--format elements'.")
    filters.add_argument("--regexp", "-e", dest="name_regexp", metavar="regexp",
                         help="A regular expression to match *only* against the basis "
                         "set name.")
    filters.add_argument("--description-regexp", "-d", metavar="regexp",
                         dest="description_regexp",
                         help="Regular expression the basis set description "
                         "should match.")
    filters.add_argument("--ignore-case", "-i", action="store_true", dest="ignorecase",
                         help="Ignore case when matching patterns")

    #
    # Formatting options
    #
    list_formats = parser.add_argument_group("Formatting options")
    list_formats.add_argument("--format", choices=available_list_formats, nargs="+",
                              metavar="flag",
                              help="Amend the default list formatting by specifying "
                              "further flags.")
    list_formats.add_argument("--extra", action="store_true",
                              help="Use the 'extra' format style when listing basis "
                              "sets. This is currently defined as '" +
                              " ".join(config.list_formats["extra"]) + "'")
    args = parser.parse_args()

    # Initial parsing:
    if args.download is not None:
        # If we want download, than append at least the default
        # format to download
        args.download.extend(config.default_download_formats)

    # Some defaults:
    highlight_elements = []
    filters = []

    # Default format:
    list_format = config.list_formats["default"]
    if args.extra:
        list_format = config.list_formats["extra"]

    # Parse args:
    if args.ignorecase:
        def case_transform(s):
            return s.lower()
    else:
        def case_transform(s):
            return s

    # Build filters
    if args.elements:
        args.elements = set(e for spec in args.elements for e in spec.split(",")
                            if len(e) > 0)
        highlight_elements = args.elements
        filters.append(lambda b: args.elements.issubset(set(b["elements"])))
        list_format.append("elements")
    if args.pattern:
        # Matches if name *or* description is matched
        reg_pattern = re.compile(case_transform(args.pattern))
        filters.append(lambda b: reg_pattern.search(case_transform(b["name"])) or
                       reg_pattern.search(case_transform(b["description"])))
    if args.name_regexp:
        reg_name = re.compile(case_transform(args.name_regexp))
        filters.append(lambda b: reg_name.search(case_transform(b["name"])))
    if args.description_regexp:
        reg_descr = re.compile(case_transform(args.description_regexp))
        filters.append(lambda b: reg_descr.search(case_transform(b["description"])))

    # Extend format is user wants it:
    if args.format is not None:
        list_format.extend(args.format)

    # Predicate which is true iff all filters are true
    # for a particular b:
    def matchall(b):
        return len(filters) == len([True for f in filters if f(b)])
    li = [b for b in cache.get_basisset_list(force_update=args.force_update)
          if matchall(b)]

    if not li:
        raise SystemExit("No basis set matched your search")

    if args.download:
        for fmt in args.download:
            download_basissets(li, fmt, destination=args.destination)
    else:
        list_basissets(li, highlight_elements=highlight_elements, fmt=list_format)
