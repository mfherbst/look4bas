#!/usr/bin/env python3


import argparse
from look4bas import api, display, store, config, elements


def add_cmd_args_to(parser):
    parser.add_argument("--force-update", action="store_true",
                        help="Force the cached database to be updated.")
    parser.add_argument("--destination", default=".", type=str, metavar="directory",
                        help="When downloading basis sets using --download store them in "
                        "this directory. (Default: '.', i.e. the current working "
                        "directory")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action='store_true', help="List the matching basis "
                      "sets (Default)")
    mode.add_argument("--download", nargs="*", metavar='format',
                      choices=store.formats,
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
    list_formats.add_argument("--extra", action="store_true",
                              help="Use the 'extra' format style when listing basis "
                              "sets. This is currently defined as '" +
                              " ".join(config.list_formats["extra"]) + "'")
    list_formats.add_argument("--format",
                              choices=display.available_display_formats, nargs="+",
                              metavar="flag",
                              help="Amend the default list formatting by specifying "
                              "further flags.")
    return parser


def cmd_post_parsing_cleanup(args):
    # TODO Ideally this should be directly integrated into the
    #      parsing done by argparse ... but I cannot be bothered right now.

    # If filtering for elements is requested, transform elements
    # to atomic numbers
    elem_list = elements.iupac_list()
    elem_symbols_lower = [e["symbol"].lower() for e in elem_list]

    def to_atnum(sym):
        return elem_symbols_lower.index(sym.lower())

    if args.elements:
        args.elements = set(
            to_atnum(e) for spec in args.elements for e in spec.split(",")
            if len(e) > 0
        )


def lookup_basissets(db, args):
    kwargs = {"regex": True, "ignore_case": bool(args.ignorecase), }

    # Build filters
    if args.elements:
        kwargs["has_atnums"] = list(args.elements)
    if args.name_regexp:
        kwargs["name"] = args.name_regexp
    if args.description_regexp:
        kwargs["description"] = args.description_regexp
    if args.pattern:
        # Matches if name *or* description is matched
        kwargs["pattern"] = args.pattern
    return db.search_basisset(**kwargs)


def display_results(args, findings):
    # display_args are the kwargs for the display function
    # which will be called further below.
    if args.elements:
        display_args = {
            "elements": True,
            "highlight_atnums": list(args.elements),
        }
    else:
        display_args = {}

    # Build format list, by considering default and extra
    # and extending further flags if the user wants this
    list_format = config.list_formats["default"]
    if args.extra:
        list_format = config.list_formats["extra"]
    if args.format is not None:
        list_format.extend(args.format)
    display_args.update(display.parse_list_format(list_format))

    print(len(findings), "basis sets matched your search:")
    display.print_basissets(findings, **display_args)


def download_results(args, db, findings):
    # Append at least the default format to download
    args.download.extend(config.default_download_formats)

    # TODO Later we probably want a more elaborate selection
    #      mechanism where one can select amongst the matches
    #      for those to be downloaded
    #
    #      I.e. ideally we would have some interactive selection
    #      mechanism here, where maybe file names can be changed
    #
    #      or basis sets can be decontracted or ...

    # Obtain missing cGTO definions by downloading them
    # from the net if required
    print("Downloading basis set data for {} basis sets:".format(len(findings)))
    for bset in findings:
        # TODO One could maybe use colour here as well with
        #      the colour scheme here and on display matching up
        print("    {:50s} (from {})".format(bset["name"], bset["source"]))
        api.amend_cgto_definitions(db, bset)

    print()
    print("Saving {} basis sets on disk:".format(len(findings)))
    for bset in findings:
        store.save_basisset(bset, args.download, args.destination)


def main():
    # Parse the commandline arguments
    parser = argparse.ArgumentParser(
        description="Commandline tool to search and download Gaussian basis sets. "
        "The tool downloads (and caches) the list of basis sets from the emsl basis set "
        "exchange (https://bse.pnl.gov/bse/portal) for offline search and allows to "
        "easily download individual basis sets from it.",
    )
    add_cmd_args_to(parser)
    args = parser.parse_args()
    cmd_post_parsing_cleanup(args)

    # Obtain cached data
    db = api.database()

    # Search for basis sets
    findings = lookup_basissets(db, args)
    if not findings:
        raise SystemExit("No basis set matched your search")

    # Since args.download may be absent or present, but without a value,
    # we cannot plainly use 'if args.download' here.
    if args.download is not None:
        download_results(args, db, findings)
    else:
        display_results(args, findings)


if __name__ == "__main__":
    main()
